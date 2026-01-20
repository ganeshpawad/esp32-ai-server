from flask import Flask, request, jsonify, Response
import struct
from threading import Lock

app = Flask(__name__)

audio_chunks = bytearray()
lock = Lock()

# MUST MATCH ESP32
SAMPLE_RATE = 16000
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
    with lock:
        audio_chunks = bytearray()
    return jsonify({"status": "ok", "message": "BUFFER_RESET"})


@app.route("/voice", methods=["POST"])
def voice():
    global audio_chunks
    chunk = request.data

    if not chunk:
        return jsonify({"status": "error", "msg": "EMPTY_CHUNK"}), 400

    with lock:
        audio_chunks.extend(chunk)
        total = len(audio_chunks)

    return jsonify({
        "status": "ok",
        "chunk_bytes": len(chunk),
        "total_bytes": total
    })


@app.route("/echo", methods=["GET"])
def echo():
    if not audio_chunks:
        return jsonify({"error": "NO_AUDIO"}), 400

    with lock:
        wav = pcm_to_wav(bytes(audio_chunks))

    return Response(wav, mimetype="audio/wav")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)

