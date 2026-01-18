 from flask import Flask, request, jsonify, send_file
import os, uuid
import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS

app = Flask(__name__)

# ================= CONFIG =================
UPLOAD_DIR = "uploads"
AUDIO_DIR = "audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

last_text = "No input yet"   # 🔥 STORED INPUT

# ================= HOME PAGE =================
@app.route("/")
def home():
    return f"""
    <h1>ESP32 AI SERVER</h1>
    <h2>Last ESP32 Input:</h2>
    <p style="font-size:24px;color:blue;">{last_text}</p>
    """

# ================= VOICE ENDPOINT =================
@app.route("/voice", methods=["POST"])
def voice():
    global last_text

    if "audio" not in request.files:
        return jsonify({"error": "No audio file"}), 400

    audio_file = request.files["audio"]
    filename = f"{uuid.uuid4()}.wav"
    filepath = os.path.join(UPLOAD_DIR, filename)
    audio_file.save(filepath)

    recognizer = sr.Recognizer()
    with sr.AudioFile(filepath) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio)
    except Exception:
        text = "Sorry, I could not understand"

    # 🔥 SAVE + DISPLAY INPUT
    last_text = text
    print("🎤 Text received from ESP32:", text)

    # ================= AI LOGIC =================
    command = "S"
    reply_text = text

    text_lower = text.lower()
    if "forward" in text_lower:
        command = "F"
        reply_text = "Moving forward"
    elif "back" in text_lower:
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

    # ================= TTS =================
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
    return send_file(os.path.join(AUDIO_DIR, filename), mimetype="audio/wav")

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

