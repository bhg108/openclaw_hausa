import re
import hashlib
from difflib import SequenceMatcher

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
    "at", "by", "from", "after", "over", "under", "into", "about", "says",
    "say", "new", "latest", "news", "amid", "before"
}

def normalize_text(text):
    return re.sub(r"\s+", " ", text.lower()).strip()

def tokenize(text):
    words = re.findall(r"[a-zA-Z0-9']+", normalize_text(text))
    return [w for w in words if len(w) > 2 and w not in STOPWORDS]

def title_similarity(a, b):
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()

def token_overlap(a, b):
    ta = set(tokenize(a))
    tb = set(tokenize(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, len(ta | tb))

def same_event(a, b):
    sim = title_similarity(a["title"], b["title"])
    overlap = token_overlap(a["title"] + " " + a["summary"], b["title"] + " " + b["summary"])
    same_category = a["category"] == b["category"]

    if sim >= 0.72:
        return True
    if overlap >= 0.32 and same_category:
        return True
    return False

def make_cluster_signature(cluster):
    joined = " | ".join(sorted(x["title"].lower() for x in cluster))
    return hashlib.md5(joined.encode("utf-8")).hexdigest()

def make_story_key(cluster):
    all_tokens = []
    for article in cluster:
        all_tokens.extend(tokenize(article["title"]))

    freq = {}
    for tok in all_tokens:
        freq[tok] = freq.get(tok, 0) + 1

    top = sorted(freq.items(), key=lambda x: (-x[1], x[0]))[:5]
    key = " ".join(word for word, _ in top)

    if not key:
        key = hashlib.md5(" ".join(a["title"] for a in cluster).encode("utf-8")).hexdigest()

    return key

def cluster_articles(articles):
    clusters = []

    for article in articles:
        placed = False

        for cluster in clusters:
            if same_event(article, cluster[0]):
                cluster.append(article)
                placed = True
                break

        if not placed:
            clusters.append([article])

    packaged = []
    for cluster in clusters:
        packaged.append({
            "signature": make_cluster_signature(cluster),
            "story_key": make_story_key(cluster),
            "articles": cluster,
            "size": len(cluster),
            "category": cluster[0]["category"],
        })

    return packaged
