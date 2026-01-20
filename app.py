from flask import Flask, request, jsonify, Response
import struct

app = Flask(__name__)

audio_chunks = bytearray()

SAMPLE_RATE = 8000
CHANNELS = 1
BITS = 16

def pcm_to_wav(pcm: bytes) -> bytes:
    byte_rate = SAMPLE_RATE * CHANNELS * BITS // 8
    block_align = CHANNELS * BITS // 8
    data_size = len(pcm)
    file_size = data_size + 36

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        file_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        CHANNELS,
        SAMPLE_RATE,
        byte_rate,
        block_align,
        BITS,
        b"data",
        data_size,
    )
    return header + pcm

@app.route("/")
def index():
    return "ESP32 ECHO SERVER RUNNING"

@app.route("/reset", methods=["POST"])
def reset():
    global audio_chunks
    audio_chunks = bytearray()
    return jsonify({"status": "ok", "message": "BUFFER_RESET"})

@app.route("/voice", methods=["POST"])
def voice():
    global audio_chunks
    chunk = request.data
    if not chunk:
        return jsonify({"status": "error"}), 400

    audio_chunks.extend(chunk)
    return jsonify({
        "status": "ok",
        "chunk_bytes": len(chunk),
        "total_bytes": len(audio_chunks)
    })

@app.route("/echo", methods=["GET"])
def echo():
    if not audio_chunks:
        return jsonify({"error": "NO_AUDIO"}), 400

    wav = pcm_to_wav(audio_chunks)
    return Response(wav, mimetype="audio/wav")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

