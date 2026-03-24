import os
from dotenv import load_dotenv

load_dotenv("/Users/mac13/danbello-news/.env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN")
if not TELEGRAM_CHAT_ID:
    raise ValueError("Missing TELEGRAM_CHAT_ID")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

CHAT_ID = int(TELEGRAM_CHAT_ID)

DATA_DIR = "/Users/mac13/danbello-news/openclaw_hausa"
DB_PATH = os.path.join(DATA_DIR, "openclaw.db")

CHECK_INTERVAL_SECONDS = 300
MAX_ENTRIES_PER_FEED = 8
MIN_CLUSTER_SCORE_TO_PUBLISH = 12
UPDATE_COOLDOWN_MINUTES = 45

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

RSS_FEEDS = [
    "https://dailytrust.com/feed/",
    "https://www.premiumtimesng.com/feed",
    "https://punchng.com/feed/",
    "https://www.vanguardngr.com/feed/",
    "https://nairametrics.com/feed/",
    "https://www.channelstv.com/feed/",
    "http://feeds.reuters.com/reuters/topNews",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.trtworld.com/rss",
    "http://rss.cnn.com/rss/edition.rss",
    "https://www.rt.com/rss/news/",
    "https://www.goal.com/feeds/en/news",
]

CATEGORY_RULES = {
    "Najeriya": [
        "nigeria", "nigerian", "abuja", "lagos", "kano", "kaduna", "sokoto",
        "maiduguri", "zamfara", "kebbi", "katsina", "bauchi", "borno", "jos",
        "tinubu", "shettima", "apc", "pdp", "naira", "cbn", "nnpc", "efcc",
        "inec", "fct", "niger delta", "arewa", "wike", "fubara", "osimhen"
    ],
    "Wasanni": [
        "football", "soccer", "champions league", "premier league", "uefa",
        "goal", "match", "coach", "player", "transfer", "fifa", "afcon",
        "osimhen", "galatasaray", "liverpool", "arsenal", "chelsea",
        "manchester", "barcelona", "real madrid", "sport"
    ],
    "Tattalin Arziki": [
        "economy", "economic", "naira", "dollar", "inflation", "oil", "gas",
        "fuel", "price", "market", "bank", "cbn", "finance", "tariff",
        "trade", "investment", "debt", "budget", "stock", "business"
    ],
    "Ilimi da Fasaha": [
        "technology", "tech", "ai", "artificial intelligence", "education",
        "school", "university", "internet", "startup", "software", "robot",
        "science", "research", "innovation"
    ],
    "Duniya": [
        "united states", "us ", "u.s.", "america", "china", "russia", "ukraine",
        "israel", "iran", "gaza", "trump", "putin", "eu", "europe", "un",
        "war", "attack", "ceasefire", "election", "sanction", "military",
        "court", "diplomacy", "summit", "president"
    ],
}

BREAKING_KEYWORDS = [
    "breaking", "urgent", "attack", "war", "ceasefire", "explosion",
    "killed", "kills", "dead", "crisis", "election", "oil", "gas",
    "sanction", "military", "strike", "bomb", "protest", "court",
    "fbi", "indictment", "collapse", "raid", "verdict", "fire",
    "flood", "blast", "hostage", "terror", "terrorist", "gunmen"
]

CATEGORY_EMOJI = {
    "Najeriya": "🇳🇬",
    "Duniya": "🌍",
    "Wasanni": "⚽",
    "Tattalin Arziki": "💰",
    "Ilimi da Fasaha": "🧠",
}

SOURCE_PRIORITY = {
    "Daily Trust": 10,
    "Premium Times Nigeria": 9,
    "Channels Television": 9,
    "Punch Newspapers": 8,
    "Vanguard News": 8,
    "Nairametrics": 8,
    "Reuters": 9,
    "BBC News": 8,
    "Al Jazeera": 8,
    "TRT World": 7,
    "CNN.com": 7,
    "RT": 6,
    "Goal.com": 7,
}
