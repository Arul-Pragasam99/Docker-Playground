import sys
import os
import time

print("Python path:", sys.path)
print("Starting Flask app...", flush=True)

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
    from nltk.metrics.distance import edit_distance
    
    import ssl
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    
    for pkg in ["punkt", "averaged_perceptron_tagger"]:
        try:
            nltk.data.find(f"tokenizers/{pkg}")
            print(f"✓ NLTK {pkg} already available", flush=True)
        except LookupError:
            print(f"Downloading NLTK {pkg}...", flush=True)
            nltk.download(pkg, quiet=False)
            print(f"✓ Downloaded {pkg}", flush=True)
except ImportError:
    print("Warning: NLTK not available, using fallback methods", flush=True)
except Exception as e:
    print(f"Warning: NLTK error: {e}", flush=True)

app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "docker-playground-ai",
        "timestamp": time.time()
    })

@app.route("/ready", methods=["GET"])
def ready():
    return jsonify({"status": "ready"}), 200

@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "Docker Command Validator API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "validate": "/validate (POST)"
        }
    })

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
        print(f"Validation error: {exc}", flush=True)
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting server on port {port}...", flush=True)
    print(f"Health check: http://localhost:{port}/health", flush=True)
    app.run(host="0.0.0.0", port=port, threaded=True, debug=False)  # ← threaded=True