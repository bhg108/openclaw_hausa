import json
import os
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
        return jsonify([])

    try:
        data = json.loads(FEED_PATH.read_text(encoding="utf-8"))

        if isinstance(data, list) and len(data) > 0:
            return jsonify([data[0]])  # return ONE-ITEM LIST

        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/latest")
def latest():
    if not FEED_PATH.exists():
        return jsonify([])

    try:
        data = json.loads(FEED_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return jsonify(data)
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/images/<path:filename>")
def images(filename):
    return send_from_directory(IMAGES_DIR, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
