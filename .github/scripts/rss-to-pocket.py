import os
import feedparser
import requests
import logging
from datetime import datetime, timedelta

# === CONFIGURATION ===
POCKET_CONSUMER_KEY = os.getenv("POCKET_CONSUMER_KEY")
POCKET_ACCESS_TOKEN = os.getenv("POCKET_ACCESS_TOKEN")
POCKET_API_URL = "https://getpocket.com/v3"
BATCH_SIZE = 100
# 2 weeks = 20160 minutes
ARTICLE_RETENTION_MINUTES = 10

RSS_FEEDS = [
    "https://plato.stanford.edu/rss/sep.xml",
    "https://www.theguardian.com/world/rss",
]

# === LOGGING SETUP ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === VALIDATION ===
def validate_credentials() -> bool:
    if not POCKET_CONSUMER_KEY or not POCKET_ACCESS_TOKEN:
        logger.error("Missing Pocket credentials. Please set POCKET_CONSUMER_KEY and POCKET_ACCESS_TOKEN.")
        return False
    return True

# === FETCH ARTICLES ===
def get_articles() -> list:
    """Get articles from all the RSS feeds."""
    articles = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:  # Get latest 5 articles from each feed
            articles.append({"url": entry.link, "tag": feed.feed.title.lower().replace(" ", "-")})
    return articles

# === SAVE ARTICLES TO POCKET ===
def save_to_pocket_batch(articles: list):
    """Save a batch of articles to Pocket with tags."""
    if not articles:
        logger.info("No articles to save.")
        return

    actions = [{"action": "add", "url": article["url"], "tags": article["tag"]} for article in articles]
    response = make_pocket_request("send", {"actions": actions})
    
    if response:
        logger.info(f"Successfully saved {len(articles)} articles to Pocket.")

# === FETCH POCKET ARTICLES ===
def get_pocket_articles():
    """Get all articles from Pocket."""
    response = make_pocket_request("get", {"count": 2000})
    return response.get("list", {}) if response else {}

# === DELETE ARTICLES FROM POCKET ===
def delete_articles_in_batch(article_ids: list):
    """Delete articles in batch from Pocket."""
    if not article_ids:
        logger.info("No articles to delete.")
        return
    
    for i in range(0, len(article_ids), BATCH_SIZE):
        batch = article_ids[i:i + BATCH_SIZE]
        actions = [{"action": "delete", "item_id": item_id} for item_id in batch]
        response = make_pocket_request("send", {"actions": actions})
        
        if response:
            logger.info(f"Successfully deleted {len(batch)} articles.")

# === CHECK ARTICLE AGE ===
def is_older_than_retention_period(time_added: str) -> bool:
    """Check if the article is older than the retention period."""
    try:
        article_added_date = datetime.utcfromtimestamp(int(time_added))
        return article_added_date < datetime.utcnow() - timedelta(minutes=ARTICLE_RETENTION_MINUTES)
    except ValueError:
        return False

# === MAKE API REQUESTS ===
def make_pocket_request(endpoint: str, params: dict):
    """Helper function to make requests to the Pocket API."""
    url = f"{POCKET_API_URL}/{endpoint}"
    params.update({
        "consumer_key": POCKET_CONSUMER_KEY,
        "access_token": POCKET_ACCESS_TOKEN
    })
    try:
        response = requests.post(url, json=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Pocket API request failed: {e}")
        return None

# === MAIN PROCESS ===
def process_articles():
    """Fetch new articles, save them to Pocket, and delete old articles."""
    if not validate_credentials():
        return

    new_articles = get_articles()
    if new_articles:
        logger.info(f"Found {len(new_articles)} new articles.")
        save_to_pocket_batch(new_articles)
    else:
        logger.info("No new articles found.")

    articles = get_pocket_articles()
    if not articles:
        logger.info("No articles found in Pocket or failed to fetch articles.")
        return

    old_articles = [article_id for article_id, article in articles.items()
                    if is_older_than_retention_period(article.get("time_added", "0"))]
    
    if old_articles:
        delete_articles_in_batch(old_articles)
    else:
        logger.info("No articles older than retention period found.")

# === EXECUTION ===
if __name__ == "__main__":
    process_articles()
