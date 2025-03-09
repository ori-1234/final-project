import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from django.utils.timezone import now
from ..models import RedditPost

class SentimentAnalyzer:
    def __init__(self):
        """
        Initialize the sentiment analyzer with the CryptoBERT model.
        """
        self.model_name = "ElKulako/cryptobert"
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        # Set up sentiment pipeline
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if torch.cuda.is_available() else -1
        )

    def analyze_sentiment(self, text):
        """
        Analyze sentiment of a given text.
        Returns a tuple (label, score).
        """
        if not text.strip():
            return "neutral", 0.0  # Default for empty text

        result = self.sentiment_pipeline(text)[0]
        return result["label"], result["score"]

    def process_posts(self):
        """
        Fetch Reddit posts with null sentiment scores, analyze them, and update the database.
        """
        posts = RedditPost.objects.filter(sentiment_score__isnull=True)

        for post in posts:
            sentiment_label, sentiment_score = self.analyze_sentiment(post.content)
            post.sentiment_score = sentiment_score
            post.save()
            print(f"Updated post {post.post_id} with sentiment {sentiment_label} ({sentiment_score})")

        print("Sentiment analysis completed.")
