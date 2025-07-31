import requests, html
from bs4 import BeautifulSoup
from datetime import datetime, timezone

def scrape_basic(url: str, selector: str, limit: int = 5):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        resp.raise_for_status()
    except Exception:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    items = []
    for tag in soup.select(selector)[:limit]:
        title = tag.get_text(strip=True)
        link = tag.get("href") or ""
        if not title or not link:
            continue
        if not link.startswith("http"):
            link = requests.compat.urljoin(url, link)
        items.append({
            "title": html.unescape(title),
            "link": link,
            "published": datetime.now(timezone.utc),
            "source": url
        })
    return items