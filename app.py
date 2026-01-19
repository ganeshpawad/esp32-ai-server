import os
import uuid
import google.generativeai as genai
from flask import Flask, request, jsonify, send_file
from gtts import gTTS

app = Flask(__name__)

# ================= CONFIGURATION =================
# Replace with your actual API key or set as environment variable in Render
API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
genai.configure(api_key=API_KEY)

# Use Gemini 1.5 Flash for speed and efficiency
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=(
        "You are an AI robot controller. I will send you audio. "
        "1. If the audio is a direction (forward, back, left, right, stop), "
        "reply with ONLY the single letter: F, B, L, R, or S. "
        "2. If it is a question or conversation, answer in one short sentence."
    )
)

AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

@app.route("/")
def index():
    return "ESP32 AI Robot Server is Running"

@app.route("/voice", methods=["POST"])
def voice():
    try:
        # Receive raw binary audio from ESP32
        audio_data = request.data
        if not audio_data:
            return jsonify({"error": "No audio data"}), 400

        # Send audio directly to Gemini Flash
        # Note: We specify the mime_type as audio/wav because we'll add 
        # a header on the ESP32 side in the next step.
        response = model.generate_content([
            "Analyze this audio command.",
            {"mime_type": "audio/wav", "data": audio_data}
        ])
        
        ai_text = response.text.strip().upper()
        
        # Determine if response is a motor command or spoken answer
        movement_cmds = ["F", "B", "L", "R", "S"]
        if any(cmd == ai_text for cmd in movement_cmds):
            command = ai_text
            reply_text = f"Moving {ai_text}"
        else:
            command = "S" # Stop motors while speaking
            reply_text = response.text

        # Convert AI reply to speech for the robot to play
        audio_filename = f"reply_{uuid.uuid4()}.wav"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        tts = gTTS(text=reply_text, lang='en')
        tts.save(audio_path)

        return jsonify({
            "command": command,
            "reply_text": reply_text,
            "audio_url": f"/audio/{audio_filename}"
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/audio/<filename>")
def get_audio(filename):
    return send_file(os.path.join(AUDIO_DIR, filename), mimetype="audio/wav")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
