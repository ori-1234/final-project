import praw
import datetime
import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

# ✅ הגדרת חיבור ל-Reddit
reddit = praw.Reddit(
    client_id="yDTOmztWHArpbYJ46LqmCA",
    client_secret="5d0vBa7KSoGHe6x1TwFgoIV513AGKw",
    user_agent="CryptoScraperBot/1.0"
)

# ✅ הגדרת המודל לניתוח סנטימנט
model_name = "ElKulako/cryptobert"
model = AutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

device = 0 if torch.cuda.is_available() else -1  # בדיקת תמיכה ב-GPU
sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, device=device)

# ✅ מילות מפתח לחיפוש בכל Reddit
target_keywords = ["bitcoin", "btc", "crypto", "blockchain", "mining", "satoshi", "decentralized", "hodl", "cryptocurrency", "Bitcoin", "BTC", "Blockchain", "Mining", "Satoshi", "Decentralized", "HODL", "Cryptocurrency"]

posts_list = []

for keyword in target_keywords:
    search_results = reddit.subreddit("all").search(keyword, limit=1000, sort="new")  # מחפש בכל Reddit לפי מילת מפתח
    
    for post in search_results:
        post_date = datetime.datetime.fromtimestamp(post.created_utc)
        full_text = f"{post.title} {post.selftext}".strip()
        
        if not full_text:
            continue  # דילוג על פוסטים ריקים
        
        # ✅ הגבלת אורך הקלט למודל
        tokens = tokenizer(
            full_text,
            return_tensors="pt",
            truncation=True,
            padding="max_length",
            max_length=512
        )

        # ✅ ניתוח סנטימנט
        sentiment_result = sentiment_pipeline(full_text[:500])[0]  # ניתוח של 500 תווים בלבד
        sentiment_label = sentiment_result['label']
        sentiment_score = sentiment_result['score']

        # ✅ שמירת הנתונים
        posts_list.append((post_date, post.title, post.selftext, post.subreddit.display_name, sentiment_label, sentiment_score))

# ✅ מיון הפוסטים לפי תאריך
posts_list.sort(reverse=True, key=lambda x: x[0])

# ✅ יצירת DataFrame ושמירת הנתונים לקובץ Excel
df = pd.DataFrame(posts_list, columns=["Date", "Title", "Post Text", "Subreddit", "Sentiment", "Sentiment Score"])
df.to_excel("reddit_sentiment_analysis.xlsx", index=False)

# ✅ הצגת כל הפוסטים שהתקבלו
for count, (post_date, post_title, post_text, sub, sentiment_label, sentiment_score) in enumerate(posts_list, start=1):
    print(f"post {count} | Date: {post_date} | Subreddit: {sub}\nTitle: {post_title}\nSentiment: {sentiment_label} ({sentiment_score:.2f})\n{post_text[:300]}...\n")  # Limit text to 300 characters
