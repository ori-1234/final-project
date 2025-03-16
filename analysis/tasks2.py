import os
import sys
import django
import requests
import datetime
import time
from django.utils import timezone
from analysis.models import RedditPost  # מודל מסד הנתונים

# 📌 1. הגדרת Django כדי שהמודלים ייטענו
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

# 📌 2. פונקציה לשליפת פוסטים ישנים מ-Pushshift API
def fetch_old_reddit_posts(keyword, start_epoch, end_epoch, limit=100):
    url = f"https://api.pushshift.io/reddit/search/submission/?q={keyword}&after={start_epoch}&before={end_epoch}&sort=desc&limit={limit}"

    try:
        response = requests.get(url, timeout=30)
        data = response.json()

        if 'data' in data:
            for post in data['data']:
                reddit_id = post['id']
                title = post['title'][:500]
                content = post.get('selftext', '')[:3000]
                created_at = timezone.make_aware(datetime.datetime.fromtimestamp(post['created_utc']))

                # בדיקה אם הפוסט כבר קיים במסד הנתונים
                if RedditPost.objects.filter(reddit_id=reddit_id).exists():
                    print(f"🚫 Skipping existing post {reddit_id}")
                    continue

                # שמירת הפוסט במסד הנתונים
                RedditPost.objects.create(
                    reddit_id=reddit_id,
                    symbol_id=1,  # לשנות בהתאם למטבע
                    title=title,
                    content=content,
                    post_num_comments=post.get('num_comments', 0),
                    post_ups=post.get('ups', 0),
                    post_author_karma=0,  # Pushshift לא מספק נתוני קארמה
                    created_at=created_at,
                    sentiment_label=None,
                    sentiment_score=None
                )

                print(f"✅ Saved post {reddit_id} | Title: {title[:50]}...")

    except requests.exceptions.RequestException as e:
        print(f"⚠ Error fetching posts: {str(e)} - Retrying in 60 seconds...")
        time.sleep(60)
        fetch_old_reddit_posts(keyword, start_epoch, end_epoch, limit)  # ניסיון נוסף

# 📌 3. פונקציה לשליפת פוסטים היסטוריים **לחודש מסוים בלבד**
def fetch_historical_posts(keyword, year, month):
    start_epoch = int(datetime.datetime(year, month, 1).timestamp())
    end_epoch = int(datetime.datetime(year, month+1, 1).timestamp()) if month < 12 else int(datetime.datetime(year+1, 1, 1).timestamp())

    print(f"🔍 Fetching posts for {keyword} from {datetime.datetime.fromtimestamp(start_epoch)} to {datetime.datetime.fromtimestamp(end_epoch)}...")
    fetch_old_reddit_posts(keyword, start_epoch, end_epoch)
    print("🎯 Historical Reddit posts fetching complete!")

# 📌 4. הרצה ישירה אם הקובץ מופעל כקובץ עצמאי (לדוגמה - ינואר 2023)
if __name__ == "__main__":
    print("✅ Running fetch_historical_posts directly")
    fetch_historical_posts("bitcoin", 2023, 1)  # שליפה לינואר 2023 בלבד
