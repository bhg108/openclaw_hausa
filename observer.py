import re
import feedparser
from config import RSS_FEEDS, MAX_ENTRIES_PER_FEED, CATEGORY_RULES

def normalize_text(text):
    return re.sub(r"\s+", " ", text.lower()).strip()

def keyword_score(text, keywords):
    return sum(1 for kw in keywords if kw in text)

def classify_category(title, summary, source):
    text = normalize_text(f"{title} {summary} {source}")
    scores = {category: keyword_score(text, words) for category, words in CATEGORY_RULES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Duniya"

def fetch_articles():
    results = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        source = getattr(feed.feed, "title", "Unknown Source")

        for entry in feed.entries[:MAX_ENTRIES_PER_FEED]:
            title = getattr(entry, "title", "").strip()
            summary = getattr(entry, "summary", "").strip()
            link = getattr(entry, "link", "").strip()
            published = getattr(entry, "published", "").strip()

            if not title or not link:
                continue

            category = classify_category(title, summary, source)

            results.append({
                "title": title,
                "summary": summary,
                "link": link,
                "source": source,
                "category": category,
                "published": published,
            })

    return results
