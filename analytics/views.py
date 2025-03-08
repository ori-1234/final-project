from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Coin, MarketData
from .cache import MarketDataCache
import json
import logging
import redis
from django.conf import settings
from collections import defaultdict
from django.utils import timezone
from rest_framework.response import Response

logger = logging.getLogger(__name__)

class MarketDataViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def market_overview(self, request):
        try:
            response_data = []
            
            # Get all coins from the Coin model
            coins = Coin.objects.all()
            
            for coin in coins:
                # Get cache data for this symbol
                cache_data = MarketDataCache.get_market_data(coin.symbol.lower()) or {}
                
                # Format numbers properly
                current_price = float(cache_data.get('current_price', 0))
                volume = float(cache_data.get('volume', 0))
                price_change = float(cache_data.get('price_change_percent_24h', 0))
                
                # Create coin data with the exact structure needed by the Grid component
                coin_data = {
                    "id": coin.symbol,
                    "name": coin.name,
                    "symbol": coin.symbol,
                    "image": coin.logo or "",
                    "desc": coin.description or "",
                    "current_price": current_price,
                    "total_volume": volume,
                    "price_change_percentage_24h": price_change,
                    "market_cap": volume * current_price,  # Calculate market cap if needed
                    "last_updated": cache_data.get('updated_at', ""),
                }
                
                # Add to response array only if we have valid price data
                if current_price > 0:
                    response_data.append(coin_data)
            
            logger.info(f"Sending market data: {json.dumps(response_data)}")
            
            # Return JSON response with proper numeric values
            return HttpResponse(
                json.dumps(response_data, default=str),  # Use default=str for datetime objects
                content_type='application/json'
            )
            
        except Exception as e:
            logger.error(f"Error in market_overview: {str(e)}")
            return HttpResponse(
                json.dumps({"error": "Failed to fetch market data"}),
                content_type='application/json',
                status=500
            )
        


class AnalyticsViewSet(viewsets.ViewSet):
    @action(detail=True, methods=['get'])
    def coin_details(self, request, pk=None):
        """
        Returns daily market data for a specific coin over multiple timeframes.
        """
        try:
            if not pk:
                return Response(
                    {"error": "Coin symbol is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            symbol = pk.upper()
            
            # 1) First verify coin exists
            coin = get_object_or_404(Coin, symbol=symbol)
            
            # 2) Try to get complete data from cache
            cached_data = MarketDataCache.get_chart_data(symbol)
            
            # 3) Get current market data
            market_data = MarketDataCache.get_market_data(coin.symbol.lower()) or {}
            
            # 4) Prepare response data
            response_data = {
                "id": coin.id,
                "name": coin.name,
                "symbol": coin.symbol,
                "logo": coin.logo or "",
                "description": coin.description or "",
                "current_price": float(market_data.get('current_price', 0)),
                "price_change_percent_24h": float(market_data.get('price_change_percent_24h', 0)),
                "high_24h": float(market_data.get('high', 0)),
                "low_24h": float(market_data.get('low', 0)),
                "volume": float(market_data.get('volume', 0)),
                "last_updated": market_data.get('updated_at', ""),
            }

            # 5) If we have cached chart data, use it
            if cached_data and cached_data.get('chart_data'):
                response_data['chart_data'] = cached_data['chart_data']
            else:
                # If no cached data, generate it now synchronously
                logger.info(f"No cached chart data for {symbol}, generating now...")
                from .tasks import update_coin_details_cache
                cache_data = update_coin_details_cache(symbol)
                if cache_data and cache_data.get('chart_data'):
                    response_data['chart_data'] = cache_data['chart_data']
                else:
                    # If still no data, return empty chart_data
                    response_data['chart_data'] = {
                        str(days): [] for days in [7, 30, 60, 90, 120, 365]
                    }

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error in coin_details for {pk}: {str(e)}")
            return Response(
                {"error": f"Failed to fetch coin details: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class CompareViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def compare_coins(self, request):
        """
        Returns cached chart data for all coins (expected: all 5 coins).
        The JSON response follows the structure:
        
            market_data[symbol] = {
                "id": coin.id,
                "name": coin.name,
                "symbol": symbol,
                "logo": coin.logo or "",
                "current_price": float(current_data.get('current_price', 0)),
                "price_change_percent_24h": float(current_data.get('price_change_percent_24h', 0)),
                "high_24h": float(current_data.get('high', 0)),
                "low_24h": float(current_data.get('low', 0)),
                "volume": float(current_data.get('volume', 0)),
                "last_updated": current_data.get('updated_at', ""),
                "chart_data": chart_data.get('chart_data', {}) if chart_data else {},
            }
        """
        try:
            coins = Coin.objects.all()  # Adjust if you want to limit to exactly 5 coins
            market_data = {}

            for coin in coins:
                symbol = coin.symbol.upper()
                # Retrieve cached chart data for this coin
                cached_data = MarketDataCache.get_chart_data(symbol)
                # Retrieve current market data for this coin
                current_data = MarketDataCache.get_market_data(symbol.lower()) or {}

                coin_data = {
                    "id": coin.id,
                    "name": coin.name,
                    "symbol": symbol,
                    "logo": coin.logo or "",
                    "current_price": float(current_data.get('current_price', 0)),
                    "price_change_percent_24h": float(current_data.get('price_change_percent_24h', 0)),
                    "high_24h": float(current_data.get('high', 0)),
                    "low_24h": float(current_data.get('low', 0)),
                    "volume": float(current_data.get('volume', 0)),
                    "last_updated": current_data.get('updated_at', ""),
                }
                
                # Use cached chart data if available; otherwise, generate it synchronously.
                if cached_data and cached_data.get('chart_data'):
                    coin_data["chart_data"] = cached_data.get('chart_data')
                else:
                    logger.info(f"No cached chart data for {symbol}, generating now...")
                    from .tasks import update_coin_details_cache
                    cache_data = update_coin_details_cache(symbol)
                    if cache_data and cache_data.get('chart_data'):
                        coin_data["chart_data"] = cache_data.get('chart_data')
                    else:
                        # Return empty chart_data for the known timeframes
                        coin_data["chart_data"] = {str(d): [] for d in [7, 30, 60, 90, 120, 365]}

                market_data[symbol] = coin_data

            return Response({"data": market_data})
        
        except Exception as e:
            logger.error(f"Error in compare_coins view: {str(e)}")
            return Response(
                {"error": f"Failed to fetch compare data: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


#     @action(detail=True, methods=['get'])
#     def coin_details(self, request, pk=None):
#         """
#         Returns detailed market data for a specific coin.
#         GET /api/market/coin_details/BTC/
#         """
#         try:
#             # Get coin from database
#             coin = get_object_or_404(Coin, symbol=pk.upper())
            
#             # Get current market data from cache
#             market_data = MarketDataCache.get_market_data(coin.symbol.lower())
            
#             if not market_data:
#                 return Response(
#                     {"error": "No market data available"}, 
#                     status=status.HTTP_404_NOT_FOUND
#                 )

#             response_data = {
#                 "symbol": coin.symbol,
#                 "name": coin.name,
#                 "logo": request.build_absolute_uri(coin.logo.url) if coin.logo else None,
#                 "description": coin.description,
#                 "market_data": {
#                     "current_price": market_data.get("current_price"),
#                     "price_change_percent_24h": market_data.get("price_change_percent_24h"),
#                     "high_24h": market_data.get("high"),
#                     "low_24h": market_data.get("low"),
#                     "volume_24h": market_data.get("volume"),
#                     "last_updated": market_data.get("updated_at")
#                 }
#             }

#             return Response(response_data)

#         except Exception as e:
#             logger.error(f"Error in coin_details: {str(e)}")
#             return Response(
#                 {"error": "Failed to fetch coin details"}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#     @action(detail=False, methods=['get'])
#     def compare(self, request):
#         """
#         Compare market data for two coins.
#         GET /api/market/compare/?symbol1=BTC&symbol2=ETH
#         """
#         try:
#             symbol1 = request.query_params.get('symbol1', '').upper()
#             symbol2 = request.query_params.get('symbol2', '').upper()
            
#             if not symbol1 or not symbol2:
#                 return Response(
#                     {"error": "Both symbol1 and symbol2 query parameters are required"}, 
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # Get coins from database
#             coins = Coin.objects.filter(symbol__in=[symbol1, symbol2])
#             if coins.count() != 2:
#                 return Response(
#                     {"error": "One or both coins not found"}, 
#                     status=status.HTTP_404_NOT_FOUND
#                 )

#             response_data = {}
#             for symbol in [symbol1, symbol2]:
#                 coin = coins.get(symbol=symbol)
#                 trading_pair = f"{symbol.lower()}usdt"
#                 market_data = MarketDataCache.get_market_data(trading_pair)

#                 if market_data:
#                     response_data[symbol] = {
#                         "name": coin.name,
#                         "logo": request.build_absolute_uri(coin.logo.url) if coin.logo else None,
#                         "market_data": {
#                             "current_price": market_data.get("current_price"),
#                             "price_change_percent_24h": market_data.get("price_change_percent_24h"),
#                             "high_24h": market_data.get("high"),
#                             "low_24h": market_data.get("low"),
#                             "volume_24h": market_data.get("volume"),
#                             "last_updated": market_data.get("updated_at")
#                         }
#                     }

#             return Response(response_data)

#         except Exception as e:
#             logger.error(f"Error in compare: {str(e)}")
#             return Response(
#                 {"error": "Failed to compare coins"}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

# class TechnicalIndicatorViewSet(viewsets.ReadOnlyModelViewSet):
#     serializer_class = TechnicalIndicatorSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         trading_pair_id = self.request.query_params.get('trading_pair')
#         indicator_type = self.request.query_params.get('type')
        
#         queryset = TechnicalIndicator.objects.filter(
#             trading_pair_id=trading_pair_id
#         ).order_by('-timestamp')
        
#         if indicator_type:
#             queryset = queryset.filter(indicator_type=indicator_type)
            
#         return queryset[:100]  # Last 100 data points