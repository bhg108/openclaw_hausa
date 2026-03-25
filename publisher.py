import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from telegram import Bot

from config import CHAT_ID, HEADERS, TELEGRAM_BOT_TOKEN

bot = Bot(token=TELEGRAM_BOT_TOKEN)

BASE_URL = "https://openclaw-hausa.onrender.com"

# Runtime-generated assets/feed
FEED_PATH = Path.home() / "danbello-news" / "openclaw_hausa" / "latest_feed.json"
IMAGES_DIR = Path.home() / "danbello-news" / "openclaw_hausa" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Repo file for Sharhi (matches api.py reading from repo dir)
REPO_DIR = Path(__file__).resolve().parent
EDITORIAL_PATH = REPO_DIR / "editorial.json"

# Editorial automation settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EDITORIAL_MODEL = os.getenv("EDITORIAL_MODEL", "gpt-4o-mini")
EDITORIAL_HOUR = int(os.getenv("EDITORIAL_HOUR", "20"))  # 8pm
EDITORIAL_MAX_STORIES = int(os.getenv("EDITORIAL_MAX_STORIES", "5"))


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
# HEADLINE / SUMMARY EXTRACTION
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

    headline = ""
    for line in cleaned:
        if len(line) > 20:
            headline = line
            break

    if not headline:
        headline = "Babban Labari"

    if len(headline) > 120:
        headline = " ".join(headline.split()[:14])

    summary = ""
    if len(cleaned) > 1:
        summary = cleaned[1]

    if len(summary) < 30 and len(cleaned) > 2:
        summary = cleaned[2]

    if not summary:
        summary = headline

    return headline, summary, text.strip()


def extract_headline_and_summary(text: str) -> tuple[str, str]:
    headline, summary, _ = extract_headline_summary_fulltext(text)
    return headline, summary


# =========================
# ARTICLE IMAGE EXTRACTION
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
# FEED WRITING
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

            # Remove duplicate story_key
            if story_key:
                existing = [
                    item for item in existing
                    if item.get("story_key", "") != story_key
                ]

            existing.insert(0, payload)
            existing = existing[:20]

            FEED_PATH.write_text(
                json.dumps(existing, ensure_ascii=False, indent=2),
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
# SHARHI AUTOMATION
# =========================
def _parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            pass
    return None


def _load_feed() -> list[dict]:
    if not FEED_PATH.exists():
        return []

    try:
        data = json.loads(FEED_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []
    except Exception:
        return []


def _top_stories_last_24h(limit: int = EDITORIAL_MAX_STORIES) -> list[dict]:
    now = datetime.now()
    cutoff = now - timedelta(hours=24)

    stories = []
    for item in _load_feed():
        dt = _parse_dt(item.get("published_at", ""))
        if dt is None:
            continue
        if dt >= cutoff:
            stories.append(item)

    stories.sort(
        key=lambda x: (
            int(x.get("relevance_score", 0) or 0),
            x.get("published_at", "")
        ),
        reverse=True,
    )

    return stories[:limit]


def _editorial_already_generated_today() -> bool:
    if not EDITORIAL_PATH.exists():
        return False

    try:
        data = json.loads(EDITORIAL_PATH.read_text(encoding="utf-8"))
        generated_for = data.get("generated_for_date", "")
        return generated_for == datetime.now().strftime("%Y-%m-%d")
    except Exception:
        return False


def _editorial_due_now() -> bool:
    now = datetime.now()
    return now.hour >= EDITORIAL_HOUR and not _editorial_already_generated_today()


def _build_editorial_prompt(stories: list[dict]) -> str:
    bullets = []
    for i, s in enumerate(stories, start=1):
        bullets.append(
            f"{i}. Take: {s.get('headline', '')}\n"
            f"Takaitaccen bayani: {s.get('summary', '')}\n"
            f"Rukuni: {s.get('category', '')}"
        )

    story_block = "\n\n".join(bullets)

    return f"""
Ka kasance mai rubuta “Sharhin Dan Bello” a Hausa mai tsauri, mai zafi, amma mai hankali da mafita.

A yau ka duba manyan labaran sa'o'i 24 da suka gabata sannan ka rubuta sharhi guda daya mai tsawo.

KA'IDOJI:
- Taken dole ya fara da: "Sharhin Dan Bello akan:"
- Rubutun ya kasance a Hausa mai sauki amma mai karfi
- Ya kasance mai cike da fushi mai ma'ana, gaskiya, da tona asirin matsala
- Ya bayyana: menene matsalar, me yasa take faruwa, wa ke wahala, wa ke cin moriya
- Dole ne ya bada hanyoyin gyara ko kariya domin kada lamarin ya maimaitu
- Ka jaddada manufar Dan Bello: gaskiya, adalci, ilimi, tsaro, da ci gaban tattalin arziki domin kare talaka
- Kada ka yi tsauri marar amfani; ka kasance mai zafi amma mai mafita
- Ka yi tsawo sosai, a matsayin cikakken editorial na rana

TSARI:
1. Layi na farko = TAKE
2. Sauran = JIKIN SHARHI
3. Karshen sharhi ya kare da layi mai karfi na "Dan Bello yace: ..."

MANYAN LABARAN SA'O'I 24:
{story_block}
""".strip()


def _call_openai_for_editorial(prompt: str) -> str:
    if not OPENAI_API_KEY:
        return ""

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": EDITORIAL_MODEL,
                "temperature": 0.8,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Kai marubucin Sharhin Dan Bello ne. "
                            "Kana rubuta Hausa mai karfi, mai zafi, mai ma'ana, "
                            "mai goyon bayan gaskiya, adalci, ilimi, tsaro da tattalin arziki mai anfani ga talaka."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return ""


def _extract_title_and_body(editorial_text: str, fallback_stories: list[dict]) -> tuple[str, str]:
    lines = [line.strip() for line in editorial_text.splitlines() if line.strip()]

    if lines:
        title = lines[0]
        body = "\n\n".join(lines[1:]).strip()
    else:
        title = ""
        body = ""

    if not title:
        first_headline = fallback_stories[0].get("headline", "Babban Lamari") if fallback_stories else "Babban Lamari"
        title = f"Sharhin Dan Bello akan: {first_headline}"

    if not title.lower().startswith("sharhin dan bello akan"):
        title = f"Sharhin Dan Bello akan: {title}"

    if not body:
        body = (
            "A yau akwai manyan abubuwa da suka nuna cewa duniya na bukatar karin gaskiya, adalci, ilimi, tsaro, "
            "da ci gaban tattalin arziki domin kare rayuwar talakawa.\n\n"
            "Dan Bello yace: Lokaci ya yi da za a daina wasa da rayuwar jama'a."
        )

    return title, body


def save_editorial(title: str, body: str, source_stories: list[dict]) -> dict:
    payload = {
        "title": title,
        "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "generated_for_date": datetime.now().strftime("%Y-%m-%d"),
        "body": body,
        "author": "Dan Bello",
        "section": "Sharhi",
        "source_story_keys": [s.get("story_key", "") for s in source_stories if s.get("story_key")],
    }

    EDITORIAL_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def maybe_generate_daily_editorial() -> dict | None:
    if not _editorial_due_now():
        return None

    stories = _top_stories_last_24h(limit=EDITORIAL_MAX_STORIES)
    if not stories:
        return None

    prompt = _build_editorial_prompt(stories)
    editorial_text = _call_openai_for_editorial(prompt)
    if not editorial_text:
        return None

    title, body = _extract_title_and_body(editorial_text, stories)
    return save_editorial(title, body, stories)


def _split_long_text(text: str, max_len: int = 3900) -> list[str]:
    text = text.strip()
    if len(text) <= max_len:
        return [text]

    parts = []
    current = ""

    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue

        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= max_len:
            current = candidate
        else:
            if current:
                parts.append(current)
            if len(para) <= max_len:
                current = para
            else:
                # hard split very long paragraph
                for i in range(0, len(para), max_len):
                    chunk = para[i:i + max_len]
                    if i == 0:
                        current = chunk
                    else:
                        parts.append(current)
                        current = chunk

    if current:
        parts.append(current)

    return parts


async def maybe_publish_editorial_to_telegram(editorial_payload: dict | None) -> None:
    if not editorial_payload:
        return

    title = editorial_payload.get("title", "Sharhin Dan Bello")
    body = editorial_payload.get("body", "")
    published_at = editorial_payload.get("published_at", "")

    combined = f"🔥 Sharhin Dan Bello\n\n{title}\n\n{published_at}\n\n{body}".strip()
    parts = _split_long_text(combined)

    for part in parts:
        await bot.send_message(chat_id=CHAT_ID, text=part)


# =========================
# PUBLISH NEWS + MAYBE SHARHI
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
        except Exception:
            await bot.send_message(chat_id=CHAT_ID, text=text)
    else:
        await bot.send_message(chat_id=CHAT_ID, text=text)

    # Generate and publish Sharhi once daily after configured hour
    editorial_payload = maybe_generate_daily_editorial()
    if editorial_payload:
        await maybe_publish_editorial_to_telegram(editorial_payload)
