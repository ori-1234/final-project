from django.apps import AppConfig
from django.utils import timezone
# from .tasks import fetch_reddit_posts  # Import the fetch_reddit_posts task


class AnalysisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analysis'

    # def ready(self):
    #     """
    #     This method is called when the application is ready.
    #     We can use it to trigger the fetch_reddit_posts task.
    #     """
    #     # Call the fetch_reddit_posts task
    #     fetch_reddit_posts.delay()  # Use .delay() to call it asynchronously
