import os
import sys
import django
import torch

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Set Django settings BEFORE any Django imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

# הוספת הנתיב של analysis כדי ש-Python יזהה את ml_models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Now we can import Django-related modules
import praw
import datetime
import time
from django.utils import timezone
from celery import shared_task
from analysis.models import RedditPost
# Comment out or remove this import if the module doesn't exist yet
from analysis.ml_models.elkulako import SentimentAnalyzer
print("🚀 tasks.py has started running!")

# Initialize Reddit API client
reddit = praw.Reddit(
    client_id="yDTOmztWHArpbYJ46LqmCA",
    client_secret="5d0vBa7KSoGHe6x1TwFgoIV513AGKw",
    user_agent="CryptoScraperBot/1.0"
)

# Define cryptocurrency keywords
keywords_mapping = {
    1: ["bitcoin halving", "bitcoin", "btc", "bitcoin lightning network"],
    2: ["ethereum", "eth", "ethereum smart contracts", "ethereum gas fees"],
    3: ["solana", "sol", "solana nfts", "solana defi"],
    4: ["xrp", "ripple", "xrp ledger", "xrp on-demand liquidity"],
    6: ["litecoin", "ltc", "litecoin halving", "litecoin transactions"],
    7: [
        "cryptocurrency", "crypto", "blockchain", "decentralized finance",
        "defi", "staking", "trading", "hodl", "altcoins",
        "crypto adoption", "crypto news"
    ]
}

@shared_task
def fetch_reddit_posts():
    print("Starting Reddit post processing")

    # 📌 הוספת ייבוא המודל וחישוב סנטימנט
    sentiment_analyzer = SentimentAnalyzer()  

    processed_count = 0
    processed_ids = set()

    for symbol_id, keywords in keywords_mapping.items():
        print(f"\nProcessing symbol_id: {symbol_id}")

        for keyword in keywords:
            print(f"\nProcessing keyword: {keyword}")
            posts_processed = 0

            try:
                search_results = reddit.subreddit("all").search(
                    keyword, limit=100, sort="new", time_filter="year"
                )

                for submission in search_results:
                    try:
                        if submission.id in processed_ids or RedditPost.objects.filter(reddit_id=submission.id).exists():
                            processed_ids.add(submission.id)
                            print(f"Skipping post {submission.id} (already in DB)")
                            continue

                        # 📌 חישוב סנטימנט על התוכן
                        analysis_text = f"{submission.title} {submission.selftext}"
                        analysis_text = " ".join(analysis_text.split()[:500])  # מגביל ל-500 מילים
                        label, score = sentiment_analyzer.analyze_sentiment(analysis_text)  # 🧠 חישוב סנטימנט

                        # שמירת הנתונים עם ציון הסנטימנט
                        RedditPost.objects.create(
                            reddit_id=submission.id,
                            symbol_id=str(symbol_id),
                            title=submission.title[:500],
                            content=submission.selftext[:3000],
                            post_num_comments=submission.num_comments,
                            post_ups=submission.ups,
                            post_author_karma=(submission.author.total_karma if submission.author else 0),
                            created_at=timezone.make_aware(datetime.datetime.fromtimestamp(submission.created_utc)),
                            sentiment_label=label,
                            sentiment_score=score  # ✅ עכשיו באמת שומר סנטימנט!
                        )

                        processed_count += 1
                        processed_ids.add(submission.id)
                        posts_processed += 1

                        print(f"✅ Saved post {submission.id} | Label: {label} | Sentiment Score: {score:.3f}")


                        time.sleep(5)

                    except Exception as e:
                        print(f"⚠ Error processing post {submission.id}: {str(e)}")
                        continue

                print(f"✅ Completed {posts_processed} posts for keyword: {keyword}")
                time.sleep(5)

            except Exception as e:
                print(f"⚠ Error processing keyword {keyword}: {str(e)}")
                time.sleep(5)
                continue

    return f"🎯 Successfully processed {processed_count} posts with sentiment analysis!"


if __name__ == "__main__":
    print("🔄 Running fetch_reddit_posts()...")
    fetch_reddit_posts()

print(torch.__version__)