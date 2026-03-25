import os
import sqlite3
from datetime import datetime, timedelta
from config import DB_PATH, DATA_DIR, UPDATE_COOLDOWN_MINUTES

os.makedirs(DATA_DIR, exist_ok=True)

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS articles (
        url TEXT PRIMARY KEY,
        title TEXT,
        summary TEXT,
        source TEXT,
        category TEXT,
        published TEXT,
        seen_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS published_clusters (
        cluster_signature TEXT PRIMARY KEY,
        story_key TEXT,
        category TEXT,
        headline TEXT,
        score REAL,
        mode TEXT,
        published_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS story_memory (
        story_key TEXT PRIMARY KEY,
        category TEXT,
        last_headline TEXT,
        last_summary TEXT,
        publish_count INTEGER DEFAULT 0,
        last_published_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def save_articles(articles):
    conn = get_conn()
    cur = conn.cursor()

    for a in articles:
        cur.execute("""
        INSERT OR IGNORE INTO articles (url, title, summary, source, category, published)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            a["link"],
            a["title"],
            a["summary"],
            a["source"],
            a["category"],
            a.get("published", "")
        ))

    conn.commit()
    conn.close()

def was_cluster_published(signature):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM published_clusters WHERE cluster_signature = ?", (signature,))
    row = cur.fetchone()
    conn.close()
    return row is not None

def mark_cluster_published(signature, story_key, category, headline, score, mode):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR INTO published_clusters
    (cluster_signature, story_key, category, headline, score, mode)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (signature, story_key, category, headline, score, mode))
    conn.commit()
    conn.close()

def get_story_memory(story_key):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT story_key, category, last_headline, last_summary, publish_count, last_published_at
    FROM story_memory
    WHERE story_key = ?
    """, (story_key,))
    row = cur.fetchone()
    conn.close()
    return row

def update_story_memory(story_key, category, headline, summary):
    conn = get_conn()
    cur = conn.cursor()

    existing = get_story_memory(story_key)
    if existing:
        publish_count = existing[4] + 1
        cur.execute("""
        UPDATE story_memory
        SET category = ?, last_headline = ?, last_summary = ?, publish_count = ?, last_published_at = CURRENT_TIMESTAMP
        WHERE story_key = ?
        """, (category, headline, summary, publish_count, story_key))
    else:
        cur.execute("""
        INSERT INTO story_memory
        (story_key, category, last_headline, last_summary, publish_count, last_published_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (story_key, category, headline, summary, 1))

    conn.commit()
    conn.close()

def story_recently_published(story_key):
    record = get_story_memory(story_key)
    if not record:
        return False

    last_published_at = record[5]
    try:
        dt = datetime.fromisoformat(last_published_at.replace(" ", "T"))
    except Exception:
        return False

    cutoff = datetime.now() - timedelta(minutes=UPDATE_COOLDOWN_MINUTES)
    return dt > cutoff
