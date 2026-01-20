from flask import Flask, request, jsonify

app = Flask(__name__)

# simple in-memory buffer (for test)
audio_chunks = bytearray()

@app.route("/")
def index():
    return "ESP32 AUDIO CHUNK SERVER RUNNING"

@app.route("/voice", methods=["POST"])
def voice():
    global audio_chunks

    chunk = request.data
    if not chunk:
        return jsonify({"status": "error", "msg": "NO_DATA"}), 400

    audio_chunks.extend(chunk)

    return jsonify({
        "status": "ok",
        "message": "AUDIO_RECEIVED",
        "chunk_bytes": len(chunk),
        "total_bytes": len(audio_chunks)
    })

@app.route("/reset", methods=["POST"])
def reset():
    global audio_chunks
    audio_chunks = bytearray()
    return jsonify({"status": "reset"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

