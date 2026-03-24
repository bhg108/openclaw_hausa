
# =========================
# Audience relevance filter
# =========================
RELEVANCE_KEYWORDS_HIGH = [
    "nigeria", "nigerian", "abuja", "kano", "kaduna", "zamfara", "sokoto",
    "katsina", "bauchi", "borno", "yobe", "gombe", "jigawa", "kebbi", "niger state",
    "tinubu", "shettima", "governor", "minister", "senate", "house of reps",
    "bandit", "terror", "attack", "kidnap", "insecurity", "military", "army", "police",
    "economy", "inflation", "naira", "fuel", "petrol", "electricity", "power", "grid",
    "school", "education", "hospital", "health", "farm", "farmer", "food", "hunger",
    "corruption", "efcc", "icpc", "court", "judge", "protest", "strike", "workers",
    "africa", "ecowas", "sahel", "sudan", "niger republic", "chad", "cameroon"
]

RELEVANCE_KEYWORDS_MEDIUM = [
    "un", "united nations", "world bank", "imf", "oil", "gas", "trade", "visa",
    "china", "usa", "uk", "france", "russia", "iran", "israel", "gaza", "palestine",
    "muslim", "mosque", "hajj", "ramadan", "islamic"
]

LOW_RELEVANCE_TOPICS = [
    "celebrity", "fashion", "red carpet", "dating", "romance", "relationship",
    "music video", "award show", "influencer", "viral dance", "reality show",
    "lifestyle trend", "beauty trend", "pop culture debate", "gaming drama"
]

SENSITIVE_LOW_PRIORITY_TOPICS = [
    "sexual orientation", "gender identity", "pride event", "adult content",
    "celebrity sexuality", "same-sex", "lgbt", "gay rights", "trans rights"
]

LEADER_PRESSURE_TERMS = [
    "tinubu", "shettima", "president", "governor", "minister",
    "senate", "house of reps", "national assembly", "apc", "pdp"
]

def relevance_score(title: str, summary: str, category: str = "") -> int:
    text = f"{title} {summary} {category}".lower()
    score = 0

    for kw in RELEVANCE_KEYWORDS_HIGH:
        if kw in text:
            score += 6

    for kw in RELEVANCE_KEYWORDS_MEDIUM:
        if kw in text:
            score += 3

    for kw in LOW_RELEVANCE_TOPICS:
        if kw in text:
            score -= 6

    for kw in SENSITIVE_LOW_PRIORITY_TOPICS:
        if kw in text:
            score -= 10

    if "nigeria" in text or "nigerian" in text:
        score += 5

    if any(x in text for x in [
        "kano", "kaduna", "zamfara", "sokoto", "katsina",
        "bauchi", "borno", "yobe", "jigawa", "gombe", "kebbi"
    ]):
        score += 8

    if any(x in text for x in [
        "hunger", "poverty", "inflation", "fuel", "electricity", "attack",
        "kidnap", "corruption", "strike", "hospital", "school", "farmer"
    ]):
        score += 7

    return score

def should_publish_story(title: str, summary: str, category: str = "") -> bool:
    score = relevance_score(title, summary, category)
    text = f"{title} {summary} {category}".lower()

    if any(term in text for term in SENSITIVE_LOW_PRIORITY_TOPICS):
        if not any(term in text for term in [
            "nigeria", "africa", "law", "court", "policy", "violence", "security"
        ]):
            return False

    if any(term in text for term in LOW_RELEVANCE_TOPICS) and score < 8:
        return False

    return score >= 10

def inject_accountability_frame(text: str, item: dict) -> str:
    joined = f"{item.get('title','')} {item.get('summary','')} {item.get('category','')}".lower()
    if any(term in joined for term in LEADER_PRESSURE_TERMS):
        kicker = (
            "\\n\\nTambayar da jama'a za su yi ita ce: mene ne shugabanni suka yi,"
            " mene ne suka kasa yi, kuma wa ke biyan kudin wannan gazawa?"
        )
        if kicker.strip() not in text:
            text = text.rstrip() + kicker
    return text

import asyncio
from config import CHECK_INTERVAL_SECONDS, MIN_CLUSTER_SCORE_TO_PUBLISH
from memory import (
    init_db, save_articles, was_cluster_published, mark_cluster_published,
    get_story_memory, update_story_memory, story_recently_published
)
from observer import fetch_articles
from clusterer import cluster_articles
from ranker import rank_clusters
from editor import generate_new_story_post, generate_update_post
from publisher import publish_cluster_post

def choose_best_publishable_cluster(clusters):
    for cluster in clusters:
        if was_cluster_published(cluster["signature"]):
            continue
        if cluster["score"] < MIN_CLUSTER_SCORE_TO_PUBLISH:
            continue
        if story_recently_published(cluster["story_key"]):
            continue
        return cluster
    return None

async def publish_cluster(cluster):
    story_record = get_story_memory(cluster["story_key"])

    if story_record:
        previous_headline = story_record[2]
        previous_summary = story_record[3]
        text = generate_update_post(cluster, previous_headline, previous_summary)
        mode = "update"
    else:
        text = generate_new_story_post(cluster)
        mode = "new"

    await publish_cluster_post(text, cluster)

    headline = cluster["articles"][0]["title"]
    summary = cluster["articles"][0]["summary"]

    mark_cluster_published(
        cluster["signature"],
        cluster["story_key"],
        cluster["category"],
        headline,
        cluster["score"],
        mode
    )

    update_story_memory(
        cluster["story_key"],
        cluster["category"],
        headline,
        summary
    )

    print(f"Published cluster as {mode}.")

async def run_once():
    print("Observing feeds...")
    articles = fetch_articles()
    print(f"Fetched articles: {len(articles)}")

    save_articles(articles)

    clusters = cluster_articles(articles)
    print(f"Story clusters: {len(clusters)}")

    ranked = rank_clusters(clusters)
    best = choose_best_publishable_cluster(ranked)

    if not best:
        print("No strong publishable cluster found.")
        return

    print("Chosen cluster:")
    print(f"  Category: {best['category']}")
    print(f"  Size: {best['size']}")
    print(f"  Score: {best['score']}")
    print(f"  Breaking: {best['breaking']}")
    print(f"  Story key: {best['story_key']}")

    await publish_cluster(best)

async def main():
    init_db()

    while True:
        try:
            await run_once()
        except Exception as e:
            print("Run error:", e)

        print(f"Sleeping for {CHECK_INTERVAL_SECONDS} seconds...")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(main())
