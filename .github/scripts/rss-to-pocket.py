import os
import feedparser
import requests

# Load Pocket API credentials from environment variables
POCKET_CONSUMER_KEY = os.getenv("POCKET_CONSUMER_KEY")
POCKET_ACCESS_TOKEN = os.getenv("POCKET_ACCESS_TOKEN")

# List of RSS feeds to check
RSS_FEEDS = [
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://www.theguardian.com/uk/technology/rss",
]

# Extract article links from RSS feeds
def get_articles():
    articles = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:  # Get latest 5 articles from each feed
            articles.append(entry.link)
    return articles

# Save articles to Pocket
def save_to_pocket(url):
    payload = {
        "consumer_key": POCKET_CONSUMER_KEY,
        "access_token": POCKET_ACCESS_TOKEN,
        "url": url
    }
    response = requests.post("https://getpocket.com/v3/add", json=payload)

    
    # Debugging: Print response details
    print(f"Trying to save: {url}")
    print(f"Response Code: {response.status_code}")
    print(f"Response Text: {response.text}")

    return response.status_code == 200



# Main script execution
if __name__ == "__main__":
    new_articles = get_articles()  # Get new articles
    for article in new_articles:
        if save_to_pocket(article):
            print(f" Saved: {article}")
        else:
            print(f"❌ Failed to save: {article}")


