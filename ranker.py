import re
from config import SOURCE_PRIORITY, BREAKING_KEYWORDS, CATEGORY_RULES

def normalize_text(text):
    return re.sub(r"\s+", " ", text.lower()).strip()

def keyword_score(text, keywords):
    return sum(1 for kw in keywords if kw in text)

def source_score(source_name):
    for source, score in SOURCE_PRIORITY.items():
        if source.lower() in source_name.lower():
            return score
    return 4

def is_breaking_cluster(cluster):
    text = normalize_text(" ".join(
        a["title"] + " " + a["summary"] for a in cluster["articles"]
    ))
    return keyword_score(text, BREAKING_KEYWORDS) >= 2

def nigeria_relevance(cluster):
    text = normalize_text(" ".join(
        a["title"] + " " + a["summary"] + " " + a["source"]
        for a in cluster["articles"]
    ))
    return keyword_score(text, CATEGORY_RULES["Najeriya"])

def breadth_score(cluster):
    unique_sources = {a["source"] for a in cluster["articles"]}
    return len(unique_sources)

def cluster_score(cluster):
    articles = cluster["articles"]
    text = normalize_text(" ".join(a["title"] + " " + a["summary"] for a in articles))

    max_source = max(source_score(a["source"]) for a in articles)
    breadth = breadth_score(cluster)
    nigeria = nigeria_relevance(cluster)
    breaking_bonus = 12 if is_breaking_cluster(cluster) else 0

    category_bonus = {
        "Najeriya": 12,
        "Tattalin Arziki": 9,
        "Wasanni": 8,
        "Duniya": 7,
        "Ilimi da Fasaha": 6,
    }.get(cluster["category"], 0)

    major_bonus = keyword_score(text, BREAKING_KEYWORDS) * 2

    score = (
        max_source +
        breadth * 2 +
        nigeria * 3 +
        category_bonus +
        breaking_bonus +
        major_bonus
    )

    cluster["score"] = score
    cluster["breaking"] = is_breaking_cluster(cluster)
    return cluster

def rank_clusters(clusters):
    scored = [cluster_score(c) for c in clusters]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored
