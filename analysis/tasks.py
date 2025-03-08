import praw

# Initialize Reddit API
reddit = praw.Reddit(
    client_id="yDTOmztWHArpbYJ46LqmCA",
    client_secret="5d0vBa7KSoGHe6x1TwFgoIV513AGKw",
    user_agent="CryptoScraperBot/1.0"
)

# Search for Bitcoin tweets
subreddit = reddit.subreddit("Bitcoin")
posts = subreddit.new(limit=1000)

count = 1
for post in posts:
    print(f"post {count}: {post.selftext}\n")
    count += 1
