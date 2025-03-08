import os
import sys
import django
import pandas as pd
import numpy as np
import ta
import logging
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta

# 1) Make sure Python can see the root folder (i.e., "back-end")
PROJECT_ROOT = r"C:\Users\Ori\Desktop\back-end"
sys.path.append(PROJECT_ROOT)

# 2) Point to your Django settings.
#    Replace 'backend.settings' with the correct folder name if it's not actually "backend".
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# 3) Now initialize Django
django.setup()

# 4) Now that Django is set up, you can safely import your models
from analytics.models import Coin, MarketData

logger = logging.getLogger(__name__)

def load_historical_data_from_csv():
    """
    Load historical data from CSV files in HistoricalData folder and save to database with technical indicators.
    """
    try:
        # Get only XRP coin
        try:
            coin = Coin.objects.get(symbol='XRP')
        except Coin.DoesNotExist:
            logger.error("XRP coin not found in database")
            return

        file_path = os.path.join(PROJECT_ROOT, 'analytics', 'HistoricalData/xrp_binance_prices_2025_add.csv')
        logger.info(f"Processing XRP data from {file_path}")
        
        # Read CSV file and sort by time
        df = pd.read_csv(file_path)
        df['Open Time'] = pd.to_datetime(df['Open Time'])
        df['Close Time'] = pd.to_datetime(df['Close Time'])
        df = df.sort_values('Open Time')
        
        # Calculate technical indicators
        df = calculate_technical_indicators(df)
        
        # Create a 24h shifted dataframe for price change calculation
        # (assuming 1-minute intervals, so 24 hours = 24*60 rows)
        df_24h_ago = df.shift(24*60)
        
        bulk_data = []
        
        for idx, row in df.iterrows():
            open_time = timezone.make_aware(row['Open Time'].to_pydatetime())
            close_time = timezone.make_aware(row['Close Time'].to_pydatetime())
            
            # Calculate 24h price change
            old_price = df_24h_ago.loc[idx, 'Close'] if idx >= 24*60 else None
            current_price = float(row['Close'])
            
            if old_price and float(old_price) > 0:
                price_change = ((current_price - float(old_price)) / float(old_price) * 100)
            else:
                price_change = 0
            
            market_data = MarketData(
                symbol=coin,
                open_time=open_time,
                close_time=close_time,
                open_price=float(row['Open']),
                high_price=float(row['High']),
                low_price=float(row['Low']),
                close_price=current_price,
                volume=float(row['Volume']),
                quote_volume=float(row['Quote Asset Volume']),
                num_trades=int(row['Number of Trades']),
                taker_buy_base_volume=float(row['Taker Buy Base Volume']),
                taker_buy_quote_volume=float(row['Taker Buy Quote Volume']),
                price_change_percent_24h=round(price_change, 2),
                
                # Add technical indicators
                rsi=round(float(row['RSI']), 2) if not pd.isna(row['RSI']) else None,
                macd=float(row['MACD']) if not pd.isna(row['MACD']) else None,
                macd_signal=float(row['MACD_Signal']) if not pd.isna(row['MACD_Signal']) else None,
                macd_hist=float(row['MACD_Hist']) if not pd.isna(row['MACD_Hist']) else None,
                bb_upper=float(row['BB_Upper']) if not pd.isna(row['BB_Upper']) else None,
                bb_middle=float(row['BB_Middle']) if not pd.isna(row['BB_Middle']) else None,
                bb_lower=float(row['BB_Lower']) if not pd.isna(row['BB_Lower']) else None
            )
            bulk_data.append(market_data)
            
            # Bulk create in chunks of 5000
            if len(bulk_data) >= 5000:
                with transaction.atomic():
                    MarketData.objects.bulk_create(
                        bulk_data,
                        batch_size=1000,
                        ignore_conflicts=True
                    )
                logger.info(f"Saved {len(bulk_data)} records for XRP")
                bulk_data = []
        
        # Save remaining records
        if bulk_data:
            with transaction.atomic():
                MarketData.objects.bulk_create(
                    bulk_data,
                    batch_size=1000,
                    ignore_conflicts=True
                )
            logger.info(f"Saved final {len(bulk_data)} records for XRP")
        
        total_records = MarketData.objects.filter(symbol=coin).count()
        logger.info(f"Total records for XRP: {total_records}")
        
    except Exception as e:
        logger.error(f"Error in load_historical_data_from_csv: {str(e)}")
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

if __name__ == '__main__':
    load_historical_data_from_csv()
