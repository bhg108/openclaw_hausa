import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from telegram import Bot

from config import CHAT_ID, HEADERS, TELEGRAM_BOT_TOKEN

bot = Bot(token=TELEGRAM_BOT_TOKEN)

BASE_URL = "https://openclaw-hausa.onrender.com"
FEED_PATH = Path.home() / "danbello-news" / "openclaw_hausa" / "latest_feed.json"
IMAGES_DIR = Path.home() / "danbello-news" / "openclaw_hausa" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# IMAGE HANDLING
# =========================
def cache_image_locally(image_url: str) -> str:
    if not image_url:
        return ""

    try:
        ext = ".jpg"
        lower = image_url.lower()
        if ".png" in lower:
            ext = ".png"
        elif ".webp" in lower:
            ext = ".webp"
        elif ".jpeg" in lower:
            ext = ".jpeg"

        name = hashlib.md5(image_url.encode("utf-8")).hexdigest() + ext
        out_path = IMAGES_DIR / name

        if not out_path.exists():
            r = requests.get(image_url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            out_path.write_bytes(r.content)

        return f"{BASE_URL}/images/{name}"
    except Exception:
        return ""


# =========================
# 🔥 STRONG HEADLINE FIX
# =========================
def extract_headline_summary_fulltext(text: str) -> tuple[str, str, str]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    skip_words = [
        "Takaitaccen bayani",
        "Manyan majiyoyi",
        "Majiyoyi",
        "Source",
        "Sources",
    ]

    cleaned = []
    for line in lines:
        lower = line.lower()

        if any(word.lower() in lower for word in skip_words):
            continue

        if line.startswith(("⚡", "🇳🇬", "🌍", "💰", "⚽", "🧠")):
            continue

        cleaned.append(line)

    # HEADLINE
    headline = ""
    for line in cleaned:
        if len(line) > 20:
            headline = line
            break

    if not headline:
        headline = "Babban Labari"

    if len(headline) > 120:
        headline = " ".join(headline.split()[:14])

    # SUMMARY
    summary = ""
    if len(cleaned) > 1:
        summary = cleaned[1]

    if len(summary) < 30 and len(cleaned) > 2:
        summary = cleaned[2]

    if not summary:
        summary = headline

    return headline, summary, text.strip()


# =========================
# IMAGE FROM ARTICLE
# =========================
def get_image_from_article(url: str) -> str | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=8)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]

        tw = soup.find("meta", attrs={"name": "twitter:image"})
        if tw and tw.get("content"):
            return tw["content"]
    except Exception:
        return None

    return None


# =========================
# 💣 FIXED SAVE FUNCTION
# =========================
def save_latest_feed(text: str, cluster: dict, image_url: str = "") -> None:
    headline, summary, full_text = extract_headline_summary_fulltext(text)
    local_image_url = cache_image_locally(image_url)

    story_key = cluster.get("story_key", "")

    payload = {
        "headline": headline,
        "summary": summary,
        "full_text": full_text,
        "category": cluster.get("category", "Labari"),
        "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "new",
        "story_key": story_key,
        "image_url": local_image_url,
        "relevance_score": cluster.get("relevance_score", 0),
    }

    for _ in range(3):
        try:
            if FEED_PATH.exists():
                existing = json.loads(FEED_PATH.read_text(encoding="utf-8"))
            else:
                existing = []

            if not isinstance(existing, list):
                existing = []

            # 🚫 REMOVE DUPLICATES
            filtered = []
            for item in existing:
                if item.get("story_key") != story_key:
                    filtered.append(item)

            # ➕ INSERT NEW STORY
            filtered.insert(0, payload)

            # ✂️ LIMIT
            filtered = filtered[:20]

            FEED_PATH.write_text(
                json.dumps(filtered, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return
        except Exception:
            time.sleep(0.2)

    FEED_PATH.write_text(
        json.dumps([payload], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# =========================
# PUBLISH
# =========================
async def publish_cluster_post(text: str, cluster: dict) -> None:
    image_url = None

    for article in cluster["articles"]:
        image_url = get_image_from_article(article["link"])
        if image_url:
            break

    save_latest_feed(text, cluster, image_url)

    if image_url:
        try:
            await bot.send_photo(
                chat_id=CHAT_ID,
                photo=image_url,
                caption=text[:1024],
            )
            return
        except Exception:
            pass

    await bot.send_message(chat_id=CHAT_ID, text=text)
