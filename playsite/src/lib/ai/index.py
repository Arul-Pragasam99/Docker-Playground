import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from dockerValidator import validate_command

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
except ImportError:
    print("Flask not found. Install with: pip install flask flask-cors")
    sys.exit(1)

try:
    import nltk
    for pkg in ["punkt", "averaged_perceptron_tagger"]:
        try:
            nltk.data.find(f"tokenizers/{pkg}")
        except LookupError:
            nltk.download(pkg, quiet=True)
except Exception:
    pass

app = Flask(__name__)
CORS(app, origins=["*"])

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