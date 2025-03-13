import feedparser
import requests
import os

# Pocket API credentials from GitHub Secrets
POCKET_CONSUMER_KEY = os.getenv("POCKET_CONSUMER_KEY")
POCKET_ACCESS_TOKEN = os.getenv("POCKET_ACCESS_TOKEN")

# List of RSS feeds
RSS_FEEDS = [
    "https://www.theatlantic.com/feed/all/",
    "http://plato.stanford.edu/rss/sep.xml",
]

# Fetch new articles
def fetch_new_articles():
    new_articles = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            article = {
                "title": entry.title,
                "url": entry.link,
            }
            new_articles.append(article)
    return new_articles

# Save articles to Pocket
def save_to_pocket(articles):
    api_url = "https://getpocket.com/v3/add"
    headers = {"Content-Type": "application/json"}
    
    for article in articles:
        payload = {
            "consumer_key": POCKET_CONSUMER_KEY,
            "access_token": POCKET_ACCESS_TOKEN,
            "url": article["url"],
            "title": article["title"],
        }
        response = requests.post(api_url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Saved: {article['title']}")
        else:
            print(f"Failed: {article['title']} - {response.text}")

# Run the process
if __name__ == "__main__":
    articles = fetch_new_articles()
    if articles:
        save_to_pocket(articles)
    else:
        print("No new articles found.")

