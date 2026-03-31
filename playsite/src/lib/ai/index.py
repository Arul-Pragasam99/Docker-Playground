"""
Docker Playground — Local AI HTTP Server
Flask micro-service that exposes /validate over HTTP.
No external AI APIs. Uses local NLP (nltk, numpy, difflib).

Start: python src/lib/ai/index.py
       (or: python -m src.lib.ai.index)
"""

import sys
import os
import json

# Make sure we can import sibling module regardless of cwd
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from dockerValidator import validate_command  # noqa: E402

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
except ImportError:
    print("Flask not found. Install with: pip install flask flask-cors")
    sys.exit(1)

# ─── Optional: download NLTK data on first run ────────────────────────────────
try:
    import nltk

    for pkg in ["punkt", "averaged_perceptron_tagger"]:
        try:
            nltk.data.find(f"tokenizers/{pkg}")
        except LookupError:
            nltk.download(pkg, quiet=True)
except Exception:
    pass  # NLTK optional — fallback logic in dockerValidator.py

# ─── App ──────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "docker-playground-ai"})


@app.route("/validate", methods=["POST"])
def validate():
    data = request.get_json(force=True, silent=True)
    if not data or "command" not in data:
        return jsonify({"error": "Missing 'command' field"}), 400

    command = str(data["command"]).strip()
    if not command:
        return jsonify({"error": "Empty command"}), 400

    try:
        result = validate_command(command)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("AI_PORT", 5001))
    print(f"🐳 Docker AI service starting on http://localhost:{port}")
    print("   Press Ctrl+C to stop.\n")
    app.run(host="0.0.0.0", port=port, debug=False)
