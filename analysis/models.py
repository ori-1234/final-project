from django.db import models
from django.utils import timezone

class RedditPost(models.Model):
    id = models.AutoField(primary_key=True)
    reddit_id = models.CharField(max_length=50)
    title = models.TextField()
    content = models.TextField()
    post_num_comments = models.IntegerField()
    post_ups = models.IntegerField()
    created_at = models.DateTimeField()
    sentiment_label = models.CharField(max_length=50)  # ✅ עמודת תווית סנטימנט חדשה
    sentiment_score = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'analysis_redditpost'
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title
