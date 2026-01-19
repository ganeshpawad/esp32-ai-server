 from flask import Flask, request, jsonify, send_file
import os, uuid
import speech_recognition as sr
from gtts import gTTS

app = Flask(__name__)

# ================= DIRECTORIES =================
UPLOAD_DIR = "uploads"
AUDIO_DIR = "audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# ================= GLOBAL STATE =================
last_text = "No input yet"
history = []   # last 10 commands

# ================= HOME PAGE =================
@app.route("/")
def home():
    history_html = "<br>".join(
        [f"{i+1}. {cmd}" for i, cmd in enumerate(history[::-1])]
    )

    return f"""
    <html>
    <head>
        <title>ESP32 AI Server</title>
    </head>
    <body style="font-family:Arial;">
        <h1>ESP32 AI Voice Server</h1>

        <h2>Status:</h2>
        <p style="font-size:20px;color:green;">
            BUTTON CONTROL MODE (ESP32)
        </p>

        <h2>Last ESP32 Input:</h2>
        <p style="font-size:24px;color:blue;">
            {last_text}
        </p>

        <h2>Command History (Latest 10)</h2>
        <p style="font-size:18px;">
            {history_html if history else "No history yet"}
        </p>
    </body>
    </html>
    """

# ================= VOICE ENDPOINT =================
@app.route("/voice", methods=["POST"])
def voice():
    global last_text, history

    if "audio" not in request.files:
        return jsonify({"error": "No audio file"}), 400

    # ---------- Save audio ----------
    audio_file = request.files["audio"]
    filename = f"{uuid.uuid4()}.wav"
    filepath = os.path.join(UPLOAD_DIR, filename)
    audio_file.save(filepath)

    # ---------- Speech to Text ----------
    recognizer = sr.Recognizer()
    with sr.AudioFile(filepath) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio)
    except Exception:
        text = ""

    print("🎤 ESP32 said:", text)

    # ---------- Defaults ----------
    command = "S"
    reply_text = "I did not understand"

    if text:
        last_text = text
        history.append(text)
        history[:] = history[-10:]
        text_lower = text.lower()

        # ---------- COMMAND LOGIC ----------
        if "forward" in text_lower:
            command = "F"
            reply_text = "Moving forward"

        elif "back" in text_lower or "backward" in text_lower:
            command = "B"
            reply_text = "Moving backward"

        elif "left" in text_lower:
            command = "L"
            reply_text = "Turning left"

        elif "right" in text_lower:
            command = "R"
            reply_text = "Turning right"

        elif "stop" in text_lower:
            command = "S"
            reply_text = "Stopping"

        else:
            reply_text = "Command not recognized"
            command = "S"

    # ---------- TEXT TO SPEECH ----------
    tts = gTTS(reply_text)
    audio_name = f"reply_{uuid.uuid4()}.wav"
    audio_path = os.path.join(AUDIO_DIR, audio_name)
    tts.save(audio_path)

    return jsonify({
        "reply_text": reply_text,
        "command": command,
        "audio_url": f"/audio/{audio_name}"
    })

# ================= AUDIO SERVE =================
@app.route("/audio/<filename>")
def get_audio(filename):
    return send_file(
        os.path.join(AUDIO_DIR, filename),
        mimetype="audio/wav"
    )

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

