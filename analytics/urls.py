from django.urls import path
from .views import MarketDataViewSet, AnalyticsViewSet, CompareViewSet

urlpatterns = [
    path('market_overview/', MarketDataViewSet.as_view({'get': 'market_overview'}), name='market-overview'),
    path('coin_details/<str:pk>/', AnalyticsViewSet.as_view({'get': 'coin_details'}), name='coin-details'),
    path('compare_coins/', CompareViewSet.as_view({'get': 'compare_coins'}), name='compare-coins'),
]