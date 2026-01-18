import os
import uuid
from flask import Flask, request, jsonify, send_file

import speech_recognition as sr
from gtts import gTTS
import google.generativeai as genai

# ===============================
# CONFIG
# ===============================
PORT = int(os.environ.get("PORT", 5000))
TEMP_DIR = "temp"

# Gemini API key from Render ENV
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ===============================
# APP INIT
# ===============================
app = Flask(__name__)
os.makedirs(TEMP_DIR, exist_ok=True)

# ===============================
# UTILS
# ===============================
def decide_command(text: str):
    text = text.lower()

    if "forward" in text:
        return "F", "Moving forward"
    if "back" in text or "backward" in text:
        return "B", "Moving backward"
    if "left" in text:
        return "L", "Turning left"
    if "right" in text:
        return "R", "Turning right"
    if "stop" in text:
        return "S", "Stopping"

    return "S", None


# ===============================
# ROUTES
# ===============================

@app.route("/", methods=["GET"])
def home():
    return "ESP32 AI Server is running"


@app.route("/voice", methods=["POST"])
def voice():

    # ---------- receive audio ----------
    if "audio" not in request.files:
        return jsonify({"error": "No audio file"}), 400

    audio_file = request.files["audio"]

    uid = str(uuid.uuid4())
    input_wav = f"{TEMP_DIR}/input_{uid}.wav"
    output_wav = f"{TEMP_DIR}/reply_{uid}.wav"

    audio_file.save(input_wav)

    # ---------- speech to text ----------
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(input_wav) as source:
            audio = recognizer.record(source)
            user_text = recognizer.recognize_google(audio)
    except Exception:
        user_text = ""

    print("USER SAID:", user_text)

    # ---------- motor intent ----------
    command, fixed_reply = decide_command(user_text)

    # ---------- Gemini response ----------
    if fixed_reply:
        reply_text = fixed_reply
    else:
        prompt = f"""
You are a helpful robot assistant.
User said: "{user_text}"
Reply in one short sentence.
"""
        try:
            response = model.generate_content(prompt)
            reply_text = response.text.strip()
        except Exception:
            reply_text = "Sorry, I could not understand"

    print("REPLY:", reply_text)
    print("COMMAND:", command)

    # ---------- TTS ----------
    tts = gTTS(reply_text)
    tts.save(output_wav)

    # ---------- response ----------
    return jsonify({
        "command": command,
        "reply_text": reply_text,
        "audio_url": f"/audio/{os.path.basename(output_wav)}"
    })


@app.route("/audio/<filename>", methods=["GET"])
def get_audio(filename):
    return send_file(f"{TEMP_DIR}/{filename}", mimetype="audio/wav")


# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
