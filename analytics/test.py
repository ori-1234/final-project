import os
import sys
import django
import pandas as pd
import numpy as np
import ta
import logging
from django.db import transaction
from datetime import timedelta

# הגדרת סביבת Django
PROJECT_ROOT = r"C:\Users\USER\Documents\ניצן\לימודים\פרויקט גמר - Cursor Ai\final-project"
sys.path.append(PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# ייבוא המודלים
from analytics.models import Coin, MarketData

logger = logging.getLogger(__name__)

def load_historical_data_from_csv():
    """
    טוען נתונים היסטוריים מתוך קובץ CSV של XRP, מחשב אינדיקטורים טכניים ושומר למסד הנתונים
    """
    try:
        # 1️⃣ טוען את המטבע XRP
        try:
            coin = Coin.objects.get(symbol='XRP')
        except Coin.DoesNotExist:
            logger.error("XRP coin not found in database")
            return

        # 2️⃣ קריאת הנתונים מקובץ CSV
        file_path = os.path.join(PROJECT_ROOT, 'analytics', 'HistoricalData', 'xrp_binance_prices_2025.csv')
        print(f"📂 Processing XRP data from {file_path}")

        df = pd.read_csv(file_path)

        # 3️⃣ מחיקת עמודה Ignore אם קיימת
        if 'Ignore' in df.columns:
            df.drop(columns=['Ignore'], inplace=True)

        # 4️⃣ המרת זמנים לפורמט datetime
        df['Open Time'] = pd.to_datetime(df['Open Time'], dayfirst=True)
        df['Close Time'] = df['Open Time'] + timedelta(minutes=1)

        # 5️⃣ ווידוא שכל העמודות המספריות הן float
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Quote Asset Volume',
                           'Number of Trades', 'Taker Buy Base Volume', 'Taker Buy Quote Volume']
        df[numeric_columns] = df[numeric_columns].astype(float)

        # 6️⃣ שינוי שמות העמודות לפני חישוב האינדיקטורים
        df.rename(columns={
            'Open Time': 'open_time',
            'Close Time': 'close_time',
            'Open': 'open_price',
            'High': 'high_price',
            'Low': 'low_price',
            'Close': 'close_price',
            'Volume': 'volume',
            'Quote Asset Volume': 'quote_volume',
            'Number of Trades': 'num_trades',
            'Taker Buy Base Volume': 'taker_buy_base_volume',
            'Taker Buy Quote Volume': 'taker_buy_quote_volume'
        }, inplace=True)

        # 7️⃣ חישוב אינדיקטורים טכניים
        df = calculate_technical_indicators(df)

        # 8️⃣ מילוי ערכים חסרים באינדיקטורים
        indicator_columns = ['RSI', 'MACD', 'MACD_Signal', 'MACD_Hist', 'BB_Upper', 'BB_Middle', 'BB_Lower', 'ATR', 'Williams_R']
        df[indicator_columns] = df[indicator_columns].fillna(0).astype(float)

        # 9️⃣ הוספת עמודת אינדיקטור שינוי מחיר
        df['price_change_indicator'] = np.where(
            df['close_price'] > df['open_price'], 1,
            np.where(df['close_price'] < df['open_price'], -1, 0)
        )
        
        # מחיקת שורות 2 עד 34 (אם הן לא רלוונטיות)
        df.drop(df.index[1:34], inplace=True)

        # 🔟 שמירת הנתונים לקובץ CSV
        df.to_csv("xrp.csv", index=False, encoding="utf-8")
        print("✅ הקובץ xrp.csv נשמר בהצלחה")

        # שמירת הנתונים למסד נתונים - בהערה (כפי שביקשת)
        # bulk_data = []
        # for _, row in df.iterrows():
        #     market_data = MarketData(
        #         symbol=coin,
        #         open_time=row['open_time'],
        #         close_time=row['close_time'],
        #         open_price=row['open_price'],
        #         high_price=row['high_price'],
        #         low_price=row['low_price'],
        #         close_price=row['close_price'],
        #         volume=row['volume'],
        #         quote_volume=row['quote_volume'],
        #         num_trades=int(row['num_trades']),
        #         taker_buy_base_volume=row['taker_buy_base_volume'],
        #         taker_buy_quote_volume=row['taker_buy_quote_volume'],
        #         rsi=row['RSI'],
        #         macd=row['MACD'],
        #         macd_signal=row['MACD_Signal'],
        #         macd_hist=row['MACD_Hist'],
        #         bb_upper=row['BB_Upper'],
        #         bb_middle=row['BB_Middle'],
        #         bb_lower=row['BB_Lower'],
        #         atr=row['ATR'],
        #         williams_r=row['Williams_R']
        #     )
        #     bulk_data.append(market_data)

        #     if len(bulk_data) >= 5000:
        #         with transaction.atomic():
        #             MarketData.objects.bulk_create(bulk_data, batch_size=1000, ignore_conflicts=True)
        #         print(f"✅ Saved {len(bulk_data)} records for LTC")
        #         bulk_data = []

        # if bulk_data:
        #     with transaction.atomic():
        #         MarketData.objects.bulk_create(bulk_data, batch_size=1000, ignore_conflicts=True)
        #     print(f"✅ Done saving LTC records!")

    except Exception as e:
        logger.error(f"Error in load_historical_data_from_csv: {str(e)}")
        raise

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    חישוב אינדיקטורים טכניים עבור הנתונים
    """
    df = df.sort_values('close_time')

    df['RSI'] = ta.momentum.RSIIndicator(df['close_price'], window=14).rsi()

    macd = ta.trend.MACD(df['close_price'], window_fast=12, window_slow=26, window_sign=9)
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Hist'] = macd.macd_diff()

    bb = ta.volatility.BollingerBands(df['close_price'], window=20, window_dev=2)
    df['BB_Upper'] = bb.bollinger_hband()
    df['BB_Middle'] = bb.bollinger_mavg()
    df['BB_Lower'] = bb.bollinger_lband()

    atr = ta.volatility.AverageTrueRange(df['high_price'], df['low_price'], df['close_price'], window=14).average_true_range()
    df['ATR'] = atr

    df['Williams_R'] = ta.momentum.WilliamsRIndicator(df['high_price'], df['low_price'], df['close_price'], lbp=14).williams_r()

    return df

if __name__ == '__main__':
    load_historical_data_from_csv()
