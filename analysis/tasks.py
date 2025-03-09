import praw
import datetime
from celery import shared_task
from .models import RedditPost  # Ensure you have a model for storing Reddit posts
from .ml_models.elkulako import SentimentAnalyzer  # Import the SentimentAnalyzer class

# Initialize Reddit API client
reddit = praw.Reddit(
    client_id="your_client_id",  # Replace with your actual client ID
    client_secret="your_client_secret",  # Replace with your actual client secret
    user_agent="your_user_agent"  # Replace with your actual user agent
)

# Define cryptocurrency-related keywords
btc_keywords = ["bitcoin", "btc", "bitcoin halving", "bitcoin lightning network"]
eth_keywords = ["ethereum", "eth", "ethereum smart contracts", "ethereum gas fees"]
sol_keywords = ["solana", "sol", "solana nfts", "solana defi"]
xrp_keywords = ["xrp", "ripple", "xrp ledger", "xrp on-demand liquidity"]
# usdc_keywords = ["usdc", "usd coin", "usdc stablecoin", "usdc reserves"]
ltc_keywords = ["litecoin", "ltc", "litecoin halving", "litecoin transactions"]
crypto_keywords = ["cryptocurrency", "crypto", "blockchain", "decentralized finance", "defi",
                   "staking", "trading", "hodl", "altcoins", "crypto adoption", "crypto news"]

# Mapping of keywords to symbol IDs
symbol_mapping = {
    **{keyword: 1 for keyword in btc_keywords},  # Assign symbol_id=1 for BTC keywords
    **{keyword: 2 for keyword in eth_keywords},
    **{keyword: 3 for keyword in sol_keywords},
    **{keyword: 4 for keyword in xrp_keywords},
    # **{keyword: 5 for keyword in usdc_keywords},
    **{keyword: 6 for keyword in ltc_keywords},
    **{keyword: 7 for keyword in crypto_keywords},
}

# Combine all keywords into a single list
target_keywords = list(symbol_mapping.keys())

def is_post_in_db(post_id):
    """
    Helper function to check if a post already exists in the database.
    """
    return RedditPost.objects.filter(post_id=post_id).exists()

@shared_task
def fetch_reddit_posts():
    """
    Fetch posts from Reddit, analyze sentiment, and store them in the database.
    """
    posts_list = []
    sentiment_analyzer = SentimentAnalyzer()  # Initialize the sentiment analyzer

    for keyword in target_keywords:
        search_results = reddit.subreddit("all").search(keyword, limit=2000, sort="new")
        
        for post in search_results:
            post_date = datetime.datetime.fromtimestamp(post.created_utc)
            full_text = f"{post.title} {post.selftext}".strip()
            
            if not full_text:
                continue  # Skip empty posts
            
            # Determine the symbol ID based on the keyword
            symbol_id = symbol_mapping.get(keyword, None)
            
            # Check if the post already exists in the database
            if not is_post_in_db(post.id):
                # Analyze sentiment
                sentiment_label, sentiment_score = sentiment_analyzer.analyze_sentiment(full_text)
                
                # Create a new RedditPost instance
                new_post = RedditPost(
                    post_id=None,
                    reddit_id=post.id,
                    symbol_id=symbol_id,
                    title=post.title,
                    content=full_text,
                    post_num_comments=post.num_comments,
                    post_ups=post.ups,
                    post_author_karma=post.author.total_karma,
                    subreddit=post.subreddit.display_name,
                    created_at=post_date,
                    sentiment_score=sentiment_score  # Store the sentiment score
                )
                posts_list.append(new_post)

    # Bulk create new posts in the database
    if posts_list:
        RedditPost.objects.bulk_create(posts_list)
        print(f"Inserted {len(posts_list)} new posts into the database.")
    else:
        print("No new posts to insert.")

