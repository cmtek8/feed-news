import locale
import json
import html
from datetime import datetime, timedelta, timezone
from pathlib import Path
import feedparser
from deep_translator import GoogleTranslator
from config import SOURCES, BASE_DIR
import scrapers
import autodiscover
from collections import Counter

# Imposta locale italiano per formattazione date
locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')

# Determina automaticamente il fuso orario locale
local_tz = datetime.now().astimezone().tzinfo

# Assicuriamoci che la cartella di output esista
BASE_DIR.mkdir(parents=True, exist_ok=True)
HTML_PATH = BASE_DIR / "index.html"

# Numero di articoli per pagina
ITEMS_PER_PAGE = 20

# Istanza del traduttore
translator = GoogleTranslator(source='auto', target='it')

def iso(dt_struct):
    try:
        # Convert struct_time to timestamp, then to local timezone-aware datetime
        import time
        ts = time.mktime(dt_struct)
        return datetime.fromtimestamp(ts, tz=local_tz)
    except Exception:
        return None


def fetch_rss(src, since):
    """Estrae elementi da una sorgente RSS, con nome opzionale"""
    url = src['url']
    feed = feedparser.parse(url)
    raw_source = src.get('name') or feed.feed.get('title', url)
    source_it = translator.translate(raw_source)
    items = []
    for e in feed.entries:
        when = iso(e.get('published_parsed') or e.get('updated_parsed'))
        if not when:
            when = datetime.now(local_tz)
        if when < since:
            continue
        title_it = translator.translate(html.unescape(e.title))
        items.append({
            'title': title_it,
            'link': e.link,
            'published': when,
            'source': source_it
        })
    return items


def fetch_category(cat, sources, since):
    bucket = []
    for src in sources:
        if src['type'] == 'rss':
            bucket.extend(fetch_rss(src, since))
        elif src['type'] == 'auto':
            rss = autodiscover.find_rss(src['url'])
            if rss:
                item_src = {'type': 'rss', 'url': rss, 'name': src.get('name')}
                bucket.extend(fetch_rss(item_src, since))
            else:
                bucket.extend(scrapers.scrape_basic(src['url'], src.get('selector', 'a'), None))
        elif src['type'] == 'scraper':
            bucket.extend(scrapers.scrape_basic(src['url'], src['selector'], None))
    seen = set()
    uniq = []
    for item in bucket:
        if item['link'] not in seen:
            seen.add(item['link'])
            item['category'] = cat
            uniq.append(item)
    return uniq


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i+size]


def main():
    # Ora e filtro negli ultimi 24h in timezone locale
    now = datetime.now(local_tz)
    since = now - timedelta(hours=24)

    all_items = []
    for cat, srcs in SOURCES.items():
        all_items.extend(fetch_category(cat, srcs, since))

    counts = Counter(item['link'] for item in all_items)
    for item in all_items:
        item['count'] = counts[item['link']]

    # Ordina per data (locale) desc poi popolarità
    all_items.sort(key=lambda x: (x['published'], x['count']), reverse=True)

    # Prepara pagine dati con formattazione ora
    pages = list(chunked(all_items, ITEMS_PER_PAGE))
    pages_data = []
    for page in pages:
        page_list = []
        for i in page:
            published_str = i['published'].strftime('%d/%m %H:%M')
            page_list.append({
                'category': i['category'],
                'title': i['title'],
                'link': i['link'],
                'published': published_str,
                'source': i['source'],
                'count': i['count']
            })
        pages_data.append(page_list)
    pages_json = json.dumps(pages_data)

    # Costruisci HTML
    html_doc = f"""<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <meta http-equiv='refresh' content='600'>
  <title>Rassegna ultime 24h – {now.strftime('%d %B %Y %H:%M')}</title>
  <style>
    body {{ font-family:sans-serif; background:#f5f5f5; color:#333; padding:20px }}
    table {{ border-collapse:collapse; width:100%; background:white; box-shadow:0 2px 4px rgba(0,0,0,0.1) }}
    th {{ background:#007acc; color:white; padding:8px; text-align:left }}
    td {{ border:1px solid #ccc; padding:6px }}
    tr:nth-child(even) {{ background:#f0f8ff }}
    a {{ color:#007acc; text-decoration:none }}
    a:hover {{ text-decoration:underline }}
    .nav {{ margin: 10px 0; }}
    .nav button {{ padding:6px 12px; margin-right:8px; }}
  </style>
</head>
<body>
  <header>
    <h1>📰 Rassegna ultime 24h – {now.strftime('%d %B %Y %H:%M')}</h1>
    <p>Notizie degli ultimi 24 ore, ordinate per data e popolarità</p>
  </header>
  <div class='nav'>
    <button id='prev' disabled>« Precedente</button>
    <span id='page-info'></span>
    <button id='next'>Successiva »</button>
  </div>
  <table>
    <thead>
      <tr><th>Categoria</th><th>Titolo</th><th>Ora</th><th>Fonte</th><th>Occorrenze</th></tr>
    </thead>
    <tbody id='news-body'></tbody>
  </table>
  <script>
    const pages = {pages_json};
    let current = 0;

    function renderNav() {{
      document.getElementById('prev').disabled = current === 0;
      document.getElementById('next').disabled = current === pages.length - 1;
      document.getElementById('page-info').textContent = `Pagina ${{current + 1}} di ${{pages.length}}`;
    }}

    function showPage(idx) {{
      current = idx;
      const tbody = document.getElementById('news-body');
      tbody.innerHTML = '';
      pages[current].forEach(i => {{
        const tr = document.createElement('tr');
        if (i.count > 1) tr.style.background = '#ffeeba';
        tr.innerHTML = `
          <td>${{i.category}}</td>
          <td><a href="${{i.link}}" target="_blank">${{i.title}}</a></td>
          <td>${{i.published}}</td>
          <td>${{i.source}}</td>
          <td>${{i.count}}</td>`;
        tbody.appendChild(tr);
      }});
      renderNav();
    }}

    document.addEventListener('DOMContentLoaded', () => {{
      document.getElementById('prev').addEventListener('click', () => {{
        if (current > 0) showPage(current - 1);
      }});
      document.getElementById('next').addEventListener('click', () => {{
        if (current < pages.length - 1) showPage(current + 1);
      }});
      showPage(0);
    }});
  </script>
</body>
</html>"""

    HTML_PATH.write_text(html_doc, encoding='utf-8')
    print(f"[OK] Saved HTML in {HTML_PATH.resolve()}")


if __name__ == "__main__":
    main()
