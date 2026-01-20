from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory buffer (test only)
audio_chunks = bytearray()

@app.route("/")
def index():
    return "ESP32 AUDIO CONFIRMATION SERVER RUNNING"

@app.route("/reset", methods=["POST"])
def reset():
    global audio_chunks
    audio_chunks = bytearray()
    print("Audio buffer reset")
    return jsonify({
        "status": "ok",
        "message": "BUFFER_RESET"
    })

@app.route("/voice", methods=["POST"])
def voice():
    global audio_chunks

    chunk = request.data
    if not chunk:
        return jsonify({
            "status": "error",
            "message": "NO_AUDIO_RECEIVED"
        }), 400

    audio_chunks.extend(chunk)

    print(f"Received chunk: {len(chunk)} bytes | Total: {len(audio_chunks)}")

    return jsonify({
        "status": "ok",
        "message": "AUDIO_CHUNK_RECEIVED",
        "chunk_bytes": len(chunk),
        "total_bytes": len(audio_chunks)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

