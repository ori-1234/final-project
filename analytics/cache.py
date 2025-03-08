import redis
import json
from django.conf import settings
from django.core.cache import cache
import logging
import requests

logger = logging.getLogger(__name__)

class MarketDataCache:
    """Cache implementation using Redis"""
    
    _redis_client = None
    
    # CoinGecko ID mapping
    COINGECKO_IDS = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
        'XRP': 'ripple',
        'USDC': 'usd-coin',
        'LTC': 'litecoin'
    }
    
    @classmethod
    def get_redis_client(cls):
        """Get or create Redis client"""
        if cls._redis_client is None:
            try:
                cls._redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=0,
                    decode_responses=True
                )
                cls._redis_client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                raise
        return cls._redis_client

    @classmethod
    def set_market_data(cls, symbol, data):
        """Set market data in cache"""
        try:
            key = f"market_data:{symbol}"
            cls.get_redis_client().set(key, json.dumps(data), ex=3600)
            logger.debug(f"Cached {key}: {data}")
        except Exception as e:
            logger.error(f"Cache set error for {symbol}: {e}")
            raise

    @classmethod
    def get_market_data(cls, symbol):
        """Get market data from cache"""
        try:
            key = f"market_data:{symbol}"
            data = cls.get_redis_client().get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Cache get error for {symbol}: {e}")
            return None


    # Add these methods to the MarketDataCache class

    @classmethod
    def set_chart_data(cls, symbol, data):
        """
        Set chart data in cache with 5 minute expiration
        
        Args:
            symbol (str): Coin symbol (e.g., 'BTC')
            data (dict): Chart data including prices, volumes, and metadata
        """
        try:
            key = f"chart_data:{symbol.lower()}"
            cls.get_redis_client().set(key, json.dumps(data), ex=300)  # 5 minutes
            logger.debug(f"Cached chart data for {symbol}")
        except Exception as e:
            logger.error(f"Cache set error for chart data {symbol}: {e}")
            raise

    @classmethod
    def get_chart_data(cls, symbol):
        """
        Get chart data from cache
        
        Args:
            symbol (str): Coin symbol (e.g., 'BTC')
            
        Returns:
            dict: Chart data if found, None otherwise
        """
        try:
            key = f"chart_data:{symbol.lower()}"
            data = cls.get_redis_client().get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Cache get error for chart data {symbol}: {e}")
            return None

    @classmethod
    def delete_chart_data(cls, symbol):
        """
        Delete chart data from cache
        
        Args:
            symbol (str): Coin symbol (e.g., 'BTC')
        """
        try:
            key = f"chart_data:{symbol.lower()}"
            cls.get_redis_client().delete(key)
            logger.debug(f"Deleted chart data cache for {symbol}")
        except Exception as e:
            logger.error(f"Cache delete error for chart data {symbol}: {e}")


    # @classmethod
    # def set_orderbook(cls, trading_pair, orderbook, timeout=timedelta(minutes=5)):
    #     key = cls.ORDERBOOK_KEY.format(trading_pair)
    #     RedisCache.set(key, orderbook, timeout=timeout)

    # @classmethod
    # def get_orderbook(cls, trading_pair):
    #     key = cls.ORDERBOOK_KEY.format(trading_pair)
    #     return RedisCache.get(key)

    # @staticmethod
    # def get_recent_trades(trading_pair_id, minutes=5):
    #     cache_key = f'recent_trades_{trading_pair_id}'
    #     trades = cache.get(cache_key)
    #     return json.loads(trades) if trades else []

    # @staticmethod
    # def cache_trade(trading_pair_id, trade_data):
    #     cache_key = f'recent_trades_{trading_pair_id}'
    #     trades = MarketDataCache.get_recent_trades(trading_pair_id)
    #     trades.append(trade_data)
        
    #     # Keep only last 5 minutes of trades
    #     cutoff_time = trade_data['timestamp'] - timedelta(minutes=5)
    #     trades = [t for t in trades if t['timestamp'] >= cutoff_time]
        
    #     cache.set(cache_key, json.dumps(trades), timeout=300)  # 5 minutes

    # @staticmethod
    # def get_market_summary(trading_pair_id):
    #     cache_key = f'market_summary_{trading_pair_id}'
    #     return cache.get(cache_key)

    # @staticmethod
    # def cache_market_summary(trading_pair_id, summary_data):
    #     cache_key = f'market_summary_{trading_pair_id}'
    #     cache.set(cache_key, summary_data, timeout=60)  # 1 minute 

# class TrendCache:
#     TREND_KEY = "trend:{}"
#     SENTIMENT_KEY = "sentiment:{}"
    
#     @classmethod
#     def set_trend(cls, trading_pair, trend_data, timeout=timedelta(hours=1)):
#         key = cls.TREND_KEY.format(trading_pair)
#         RedisCache.set(key, trend_data, timeout=timeout)

#     @classmethod
#     def get_trend(cls, trading_pair):
#         key = cls.TREND_KEY.format(trading_pair)
#         return RedisCache.get(key) 