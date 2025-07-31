import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import feedparser

def find_rss(url):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
    except:
        return None
    soup = BeautifulSoup(resp.text, "html.parser")
    # look for link rel="alternate" RSS or Atom
    for tag in soup.find_all("link", rel="alternate"):
        t = tag.get("type", "")
        if "rss" in t or "atom" in t:
            href = tag.get("href")
            if href:
                return urljoin(url, href)
    # fallback: try parsing url as feed
    parsed = feedparser.parse(url)
    if parsed.entries:
        return url
    return None