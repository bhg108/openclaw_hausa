import json
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = Path.home() / "danbello-news" / "openclaw_hausa"
FEED_PATH = BASE_DIR / "latest_feed.json"
IMAGES_DIR = BASE_DIR / "images"

@app.route("/")
def home():
    return jsonify({"status": "ok", "service": "openclaw_hausa_api"})

@app.route("/top-story")
def top_story():
    if not FEED_PATH.exists():
        return jsonify({"error": "No feed file found"}), 404

    try:
        data = json.loads(FEED_PATH.read_text(encoding="utf-8"))
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from memory import get_conn
from flask import jsonify

@app.route("/latest")
def latest():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT headline, category, published_at, story_key, score
        FROM published_clusters
        ORDER BY published_at DESC
        LIMIT 20
    """)

    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "headline": r[0],
            "category": r[1],
            "published_at": r[2],
            "story_key": r[3],
            "score": r[4],
        })

    return jsonify(result)


@app.route("/images/<path:filename>")
def images(filename):
    return send_from_directory(IMAGES_DIR, filename)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
