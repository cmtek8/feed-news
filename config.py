from pathlib import Path

# Base directory per output
BASE_DIR = Path(r"C:\Python\feed_news_project")

# Numero massimo di articoli per categoria
# Impostalo a None per non avere alcun limite
NUM_ARTICLES = None

# Definizione delle fonti per ciascuna categoria
def typical_rss(url, name=None):
    entry = {"type": "rss", "url": url}
    if name:
        entry["name"] = name
    return entry

SOURCES = {
    "finanza": [
        {"type": "auto", "url": "https://www.finanzaonline.com/", "name": "FinanzaOnline"},
    
        typical_rss("https://www.soldionline.it/feed/", name="SoldiOnline"),
    ],
    "genova": [
        typical_rss("https://www.genova24.it/feed/", name="Genova24"),
        typical_rss("https://www.primocanale.it/?feed=rss2", name="Primocanale"),
    ],
    "notizie": [
        typical_rss("https://www.ansa.it/sito/ansait_rss.xml", name="ANSA"),
    ],
}
