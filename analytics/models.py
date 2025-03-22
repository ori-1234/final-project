from django.db import models

class Coin(models.Model):
    SYMBOLS = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('SOL', 'Solana'),
        ('XRP', 'XRP'),
        ('USDC', 'USD Coin'),
        ('LTC', 'Litecoin'),
    ]

    symbol = models.CharField(max_length=10, choices=SYMBOLS, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    logo = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.symbol


class MarketData(models.Model):
    symbol = models.ForeignKey(Coin, related_name='market_data', on_delete=models.CASCADE)
    open_time = models.DateTimeField()
    close_time = models.DateTimeField()
    open_price = models.DecimalField(max_digits=20, decimal_places=8)
    high_price = models.DecimalField(max_digits=20, decimal_places=8)
    low_price = models.DecimalField(max_digits=20, decimal_places=8)
    close_price = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=32, decimal_places=8)
    quote_volume = models.DecimalField(max_digits=32, decimal_places=8)
    num_trades = models.PositiveIntegerField()
    taker_buy_base_volume = models.DecimalField(max_digits=32, decimal_places=8, null=True, default=0)
    taker_buy_quote_volume = models.DecimalField(max_digits=32, decimal_places=8, null=True, default=0)
    price_change_percent_24h = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=0)
    
    # 📉 Technical Indicators
    rsi = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    macd = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    macd_signal = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    macd_hist = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    bb_upper = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    bb_middle = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    bb_lower = models.DecimalField(max_digits=20, decimal_places=8, null=True)

    # 🆕 הוספת ATR ו-Williams %R
    atr = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    williams_r = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['symbol', 'close_time']),
            models.Index(fields=['close_time']),
        ]
        unique_together = ('symbol', 'close_time')
        ordering = ['-close_time']  # Default to newest first

    def __str__(self):
        return f"{self.symbol.symbol} - {self.close_time}"
