from django.db import models

class RedditPost(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-generated primary key
    reddit_id = models.CharField(max_length=255, unique=True)  # Unique Reddit post ID
    symbol_id = models.CharField(max_length=50)  # Symbol ID for categorization
    title = models.TextField()
    content = models.TextField()
    post_num_comments = models.IntegerField()  # Number of comments
    post_ups = models.IntegerField()  # Number of upvotes
    post_author_karma = models.IntegerField()  # Author's total karma
    created_at = models.DateTimeField()
    sentiment_score = models.FloatField(null=True, blank=True)  # Sentiment analysis score

    def __str__(self):
        return self.title
