import os
import feedparser
import requests
import logging
from datetime import datetime

# === CONFIGURATION ===
POCKET_CONSUMER_KEY = os.getenv("POCKET_CONSUMER_KEY")
POCKET_ACCESS_TOKEN = os.getenv("POCKET_ACCESS_TOKEN")
POCKET_API_URL = "https://getpocket.com/v3"
BATCH_SIZE = 100

RSS_FEEDS = [
    {"url": "https://plato.stanford.edu/rss/sep.xml", "num_articles": 5},
    {"url": "https://www.theguardian.com/world/rss", "num_articles": 10},
    {"url": "https://feeds.skynews.com/feeds/rss/world.xml", "num_articles": 1}

    # economist
    # comic


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
    for feed in RSS_FEEDS:
        feed_data = feedparser.parse(feed["url"])
        for entry in feed_data.entries[:feed["num_articles"]]:
            articles.append({"url": entry.link, "tag": feed_data.feed.title.lower().replace(" ", "-")})
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

# === DELETE EXCESS ARTICLES ===
def delete_excess_articles():
    """Ensure only the latest articles are kept per feed."""
    articles = get_pocket_articles()
    if not articles:
        logger.info("No articles found in Pocket or failed to fetch articles.")
        return
    
    articles_by_feed = {}
    for article_id, article in articles.items():
        tags = article.get("tags", {})
        for tag_data in tags.values():
            feed_tag = tag_data["tag"]
            if feed_tag not in articles_by_feed:
                articles_by_feed[feed_tag] = []
            articles_by_feed[feed_tag].append((article_id, int(article.get("time_added", "0"))))
    
    articles_to_delete = []
    for feed in RSS_FEEDS:
        feed_tag = feed["url"].split("/")[-2]  # Extract a unique identifier from URL
        if feed_tag in articles_by_feed:
            sorted_articles = sorted(articles_by_feed[feed_tag], key=lambda x: x[1], reverse=True)
            excess_articles = sorted_articles[feed["num_articles"]:]
            articles_to_delete.extend([article[0] for article in excess_articles])
    
    if articles_to_delete:
        delete_articles_in_batch(articles_to_delete)
    else:
        logger.info("No excess articles to delete.")

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

# === EXECUTION ===
if __name__ == "__main__":
    if validate_credentials():
        new_articles = get_articles()
        if new_articles:
            logger.info(f"Found {len(new_articles)} new articles.")
            save_to_pocket_batch(new_articles)
        else:
            logger.info("No new articles found.")
        delete_excess_articles()
