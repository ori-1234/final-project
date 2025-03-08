from rest_framework import serializers
from .models import MarketData, Coin
# from .models import TechnicalIndicator

class CoinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coin
        fields = '__all__'

class MarketDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketData
        fields = '__all__'

# class TechnicalIndicatorSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TechnicalIndicator
#         fields = '__all__'