import praw
import datetime
import pandas as pd

# ✅ הגדרת חיבור ל-Reddit
reddit = praw.Reddit(
    client_id="yDTOmztWHArpbYJ46LqmCA",
    client_secret="5d0vBa7KSoGHe6x1TwFgoIV513AGKw",
    user_agent="CryptoScraperBot/1.0"
)

# ✅ מילות מפתח לחיפוש בכל Reddit
target_keywords = ["bitcoin", "btc", "crypto", "blockchain", "mining", "satoshi", "decentralized", "hodl", "cryptocurrency"]

# ✅ רשימה לאחסון הפוסטים שנמצאו
posts_list = []

# ✅ חיפוש פוסטים לכל מילת מפתח
for keyword in target_keywords:
    search_results = reddit.subreddit("all").search(
        keyword, limit=1000, sort="new", time_filter="year"
    )

    for post in search_results:
        post_date = datetime.datetime.fromtimestamp(post.created_utc)
        post_title = post.title
        post_text = post.selftext
        post_subreddit = post.subreddit.display_name

        # ✅ שמירת המידע ברשימה
        posts_list.append((post_date, post_title, post_text, post_subreddit))

# ✅ מיון הפוסטים לפי תאריך מהחדש לישן
posts_list.sort(reverse=True, key=lambda x: x[0])

# ✅ יצירת DataFrame ושמירת הנתונים בקובץ Excel
df = pd.DataFrame(posts_list, columns=["Date", "Title", "Post Text", "Subreddit"])
df.to_excel("reddit_posts.xlsx", index=False)

# ✅ הצגת סיכום התוצאות
print(f"Total posts fetched: {len(posts_list)}")
for count, (post_date, post_title, post_text, sub) in enumerate(posts_list[:200], start=1):
    print(f"post {count} | Date: {post_date} | Subreddit: {sub}\nTitle: {post_title}\n{post_text[:300]}...\n")
