from django.apps import AppConfig
from django.conf import settings

class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'

    def ready(self):
        # Only run in main process
        import os
        if os.environ.get('RUN_MAIN'):
            self.initialize_services()

    def initialize_services(self):
        try:
            # Import here to avoid circular imports
            from .consumers import BinanceWebSocketConsumer
            from .tasks import update_all_coin_details
            
            # Initialize WebSocket
            binance_ws_manager = BinanceWebSocketConsumer()
            binance_ws_manager.start()
            
            # Run initial cache update
            update_all_coin_details.delay()
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error initializing analytics services: {str(e)}")
