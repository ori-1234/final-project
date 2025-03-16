import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
import re
import numpy as np
from django.utils.timezone import now
from ..models import RedditPost

class SentimentAnalyzer:
    def __init__(self):
        try:
            self.model_name = "ElKulako/cryptobert"
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.device = 0 if torch.cuda.is_available() else -1

            # Sentiment pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=self.device
            )
            print(f"Device set to use {'CUDA' if self.device == 0 else 'CPU'}")
        except Exception as e:
            print(f"Error initializing SentimentAnalyzer: {str(e)}")
            raise

    def preprocess_text(self, text):
        """Preprocesses input text by removing links, mentions, hashtags, and special characters."""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE)
        text = re.sub(r"@\w+|#", "", text)
        text = re.sub(r"[^a-z\s]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def analyze_sentiment(self, text):
        """
        Returns a tuple: (label_string, numeric_score).
        label_string can be 'Bullish', 'Bearish', 'Neutral'.
        numeric_score is exactly what the model returns, without any multiplications.
        """
        try:
            cleaned = self.preprocess_text(text)
            if not cleaned:
                return ("Neutral", 0.0)
            
            result = self.sentiment_pipeline(cleaned[:512])[0]
            raw_label = result["label"]
            raw_score = result["score"]
            
            # Add debug print
            # print(f"DEBUG - Raw model output: Label={raw_label}, Score={raw_score}")
            
            # Map labels. Adjust as needed for your model's output
            sentiment_map = {
                "Bullish": 1,
                "Bearish": -1,
                "Neutral": 0,
            }

            # If label unknown, fallback to neutral
            if raw_label not in sentiment_map:
                print(f"Warning: Unrecognized label '{raw_label}'. Defaulting to neutral.")
                return ("Neutral", raw_score)  # ✅ ציון מוחזר כמות שהוא

            return (raw_label, raw_score)  # Should return exactly what the model gives us

        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            return ("Neutral", 0.0)
