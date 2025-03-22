from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
from .models import MarketData, Coin
from .cache import MarketDataCache
import requests
import pandas as pd
import logging
from django.db import transaction
from django.db.models import Q
import ta
from django.core.cache import cache
from typing import Optional, Dict, Any
from collections import defaultdict
import numpy as np  # תוסיף את זה בתחילת הקובץ


logger = logging.getLogger(__name__)

@shared_task
def update_coin_details_cache(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Update cache for a specific coin with daily (1 data point per day) 
    price data. We group by each calendar day and choose the last close_price
    for that day, similar to CoinGecko's daily historical approach.
    """
    try:
        logger.info(f"Starting chart data update for {symbol}")

        coin = Coin.objects.get(symbol=symbol.upper())

        latest_record = MarketData.objects.filter(symbol=coin).order_by('-close_time').first()
        if not latest_record:
            logger.warning(f"No market data found for {symbol}. Skipping.")
            return None

        end_date = latest_record.close_time

        timeframes = [7, 30, 60, 90, 120, 365]
        chart_data = {}

        for days in timeframes:
            start_date = end_date - timezone.timedelta(days=days)

            # Fetch all records in [start_date, end_date] ascending
            records = (
                MarketData.objects
                .filter(symbol=coin, close_time__gte=start_date, close_time__lte=end_date)
                .order_by('close_time')
                .values('close_time', 'close_price')
            )

            # Group by date, picking the final close_time per day
            daily_map = {}
            for r in records:
                if not r['close_price']:
                    continue

                day_key = r['close_time'].date()
                if day_key not in daily_map or r['close_time'] > daily_map[day_key]['close_time']:
                    daily_map[day_key] = {
                        'close_time': r['close_time'],
                        'close_price': float(r['close_price'])
                    }

            # Build daily data (ts, price)
            daily_data = []
            for day_key in sorted(daily_map.keys()):
                rec = daily_map[day_key]
                ts = int(rec['close_time'].timestamp() * 1000)
                daily_data.append([ts, rec['close_price']])

            # Note: we changed the log message here
            logger.info(f"Timeframe {days}d -> {len(daily_data)} daily points for {symbol}")
            chart_data[str(days)] = daily_data

        cache_data = {"chart_data": chart_data}
        MarketDataCache.set_chart_data(symbol, cache_data)
        logger.info(f"Successfully cached chart data for {symbol}")

        return cache_data

    except Coin.DoesNotExist:
        logger.error(f"Coin {symbol} does not exist.")
        return None
    except Exception as e:
        logger.error(f"Error updating chart data cache for {symbol}: {e}")
        return None




@shared_task
def update_all_coin_details():
    """
    Update cache for all active coins.
    Runs on server startup and once daily at midnight.
    """
    try:
        logger.info("Starting full update of coin details")
        coins = Coin.objects.all()
        
        if not coins.exists():
            logger.warning("No coins found in database")
            return
            
        for coin in coins:
            try:
                # Run update synchronously since this is a daily task
                update_coin_details_cache(coin.symbol)
                logger.info(f"Updated data for {coin.symbol}")
            except Exception as e:
                logger.error(f"Error updating {coin.symbol}: {str(e)}")
                continue
                
        logger.info("Completed full update of coin details")
                
    except Exception as e:
        logger.error(f"Error in update_all_coin_details: {str(e)}")


@shared_task(bind=True, max_retries=3)
def fetch_missing_klines(self):
    """Fetch missing 1-minute klines data when server starts."""
    try:
        coins = Coin.objects.all()
        now = timezone.now()

        for coin in coins:
            try:
                latest_record = MarketData.objects.filter(
                    symbol=coin
                ).order_by('-close_time').first()

                start_time = latest_record.close_time if latest_record else (now - timedelta(days=1))
                
                logger.info(f"Fetching missing data for {coin.symbol} from {start_time} to {now}")
                
                df = fetch_klines_data(coin.symbol, start_time, now)
                if df is not None and not df.empty:
                    df = calculate_technical_indicators(df)
                    process_and_store_data(coin, df)
                    
                    # עדכון מטמון אחרי אחסון הנתונים
                    update_coin_details_cache.delay(coin.symbol)

                    # ✅ הדפסה של שם המטבע והמחיר האחרון שלו
                    last_price = df.iloc[-1]['Close']
                    print(f"📈 {coin.symbol}: {last_price:.2f} USDT")

            except Exception as e:
                logger.error(f"Error processing {coin.symbol}: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error in fetch_missing_klines: {str(e)}")
        self.retry(exc=e, countdown=60)



def calculate_24h_price_change(coin: Coin, current_price: float, current_time: datetime) -> float:
    """
    Calculate 24-hour price change percentage.
    Args:
        coin: Coin model instance
        current_price: Current price of the coin
        current_time: Current timestamp
    Returns:
        float: Price change percentage
    """
    cache_key = f"price_change_{coin.symbol}_{current_time.timestamp()}"
    cached_value = cache.get(cache_key)
    if cached_value is not None:
        return cached_value

    try:
        day_ago = current_time - timedelta(hours=24)
        old_price_record = MarketData.objects.filter(
            symbol=coin,
            close_time__lte=day_ago
        ).order_by('-close_time').first()

        if old_price_record and old_price_record.close_price > 0:
            # המרה ל-float כדי למנוע TypeError
            old_price = float(old_price_record.close_price)
            price_change = ((current_price - old_price) / old_price) * 100
            result = round(price_change, 2)

            cache.set(cache_key, result, timeout=60)  # Cache for 1 minute
            return result
        return 0
    except Exception as e:
        logger.error(f"Error calculating price change for {coin.symbol}: {str(e)}")
        return 0



def fetch_klines_data(symbol: str, start_time: datetime, end_time: datetime) -> Optional[pd.DataFrame]:
    """
    Fetch 1-minute klines data from Binance API.
    Args:
        symbol: Trading pair symbol
        start_time: Start timestamp
        end_time: End timestamp
    Returns:
        Optional[pd.DataFrame]: DataFrame with klines data or None if error
    """
    base_url = 'https://api.binance.com/api/v3/klines'
    formatted_symbol = f"{symbol.upper()}USDT"
    
    params = {
        'symbol': formatted_symbol,
        'interval': '1m',
        'startTime': int(start_time.timestamp() * 1000),
        'endTime': int(end_time.timestamp() * 1000),
        'limit': 1000
    }

    all_data = []
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            while True:
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if not data:
                    break

                all_data.extend(data)
                params['startTime'] = data[-1][6] + 1

                if params['startTime'] > params['endTime']:
                    break

            if not all_data:
                logger.warning(f"No data returned for {symbol}")
                return None

            columns = [
                'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume',
                'Close Time', 'Quote Asset Volume', 'Number of Trades',
                'Taker Buy Base Volume', 'Taker Buy Quote Volume', 'Ignore'
            ]
            df = pd.DataFrame(all_data, columns=columns)

            # Convert timestamps to datetime
            df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms', utc=True)
            df['Close Time'] = pd.to_datetime(df['Close Time'], unit='ms', utc=True)


            # Convert numeric columns
            numeric_columns = [
                'Open', 'High', 'Low', 'Close', 'Volume',
                'Quote Asset Volume', 'Number of Trades',
                'Taker Buy Base Volume', 'Taker Buy Quote Volume'
            ]
            df[numeric_columns] = df[numeric_columns].astype(float)

            return df

        except requests.exceptions.RequestException as e:
            retry_count += 1
            logger.warning(f"Retry {retry_count} for {symbol}: {str(e)}")
            if retry_count == max_retries:
                logger.error(f"Max retries reached for {symbol}: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"Error fetching klines for {symbol}: {str(e)}")
            return None


def process_and_store_data(coin: Coin, df: pd.DataFrame) -> None:
    """Process and store market data with technical indicators."""
    try:
        # 🛠️ שינוי השיטה של fillna כך שתעבוד על כל העמודות
        df = df.fillna(value=0)  # מחליף NaN ב-0 לכל הנתונים המספריים

        bulk_data = []
        for _, row in df.iterrows():
            price_change = calculate_24h_price_change(
                coin=coin,
                current_price=float(row['Close']),
                current_time=row['Close Time']
            )

            market_data = MarketData(
                symbol=coin,
                open_time=row['Open Time'],
                close_time=row['Close Time'],
                open_price=row['Open'],
                high_price=row['High'],
                low_price=row['Low'],
                close_price=row['Close'],
                volume=row['Volume'],
                quote_volume=row['Quote Asset Volume'],
                num_trades=row['Number of Trades'],
                taker_buy_base_volume=row['Taker Buy Base Volume'],
                taker_buy_quote_volume=row['Taker Buy Quote Volume'],
                price_change_percent_24h=price_change,
                rsi=row.get('RSI', None),
                macd=row.get('MACD', None),
                macd_signal=row.get('MACD_Signal', None),
                macd_hist=row.get('MACD_Hist', None),
                bb_upper=row.get('BB_Upper', None),
                bb_middle=row.get('BB_Middle', None),
                bb_lower=row.get('BB_Lower', None)
            )
            bulk_data.append(market_data)

        with transaction.atomic():
            MarketData.objects.bulk_create(
                bulk_data,
                batch_size=1000,
                ignore_conflicts=True
            )

        logger.info(f"Added {len(bulk_data)} records for {coin.symbol}")

    except Exception as e:
        logger.error(f"Error in process_and_store_data for {coin.symbol}: {str(e)}")
        raise



def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate technical indicators for market data."""
    try:
        df = df.sort_values('Close Time')
        
        # Calculate RSI
        rsi = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        
        # Calculate MACD
        macd = ta.trend.MACD(df['Close'], window_fast=12, window_slow=26, window_sign=9)
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Hist'] = macd.macd_diff()
        
        # Calculate Bollinger Bands
        bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
        df['BB_Upper'] = bb.bollinger_hband()
        df['BB_Middle'] = bb.bollinger_mavg()
        df['BB_Lower'] = bb.bollinger_lband()
        
        df['RSI'] = rsi
        
        return df

    except Exception as e:
        logger.error(f"Error calculating technical indicators: {str(e)}")
        return df

