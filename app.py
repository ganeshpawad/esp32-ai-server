from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return "ESP32 AUDIO TEST SERVER RUNNING"

@app.route("/voice", methods=["POST"])
def voice():
    audio_data = request.data

    if not audio_data:
        return jsonify({
            "status": "error",
            "message": "NO_AUDIO_RECEIVED"
        }), 400

    print(f"Received audio bytes: {len(audio_data)}")

    return jsonify({
        "status": "ok",
        "message": "AUDIO_RECEIVED",
        "bytes": len(audio_data)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

