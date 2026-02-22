"""
English to Santali (Ol Chiki) Translator
=========================================
- Takes English voice input from microphone (via browser)
- Converts English speech to text using OpenAI Whisper
- Translates English text to Santali (Ol Chiki script)
- Displays Santali text in Ol Chiki script
"""

import os
import sys
import shutil
import subprocess
import tempfile
import traceback
import warnings
import requests as http_requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Suppress FP16 warnings on CPU
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)
CORS(app)   # Allow cross-origin requests (helps when port/host differ)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload

# ---------------------------------------------------------------------------
# FFmpeg check — Whisper REQUIRES ffmpeg to decode audio
# ---------------------------------------------------------------------------
def check_ffmpeg():
    """Verify ffmpeg is installed and on PATH."""
    if shutil.which("ffmpeg"):
        print("✅ ffmpeg found:", shutil.which("ffmpeg"))
        return True
    print("❌ ERROR: ffmpeg is NOT installed or not on PATH!")
    print("   Whisper cannot work without ffmpeg.")
    print("   Install it:")
    print("     Windows  → choco install ffmpeg   (or download from https://ffmpeg.org)")
    print("     macOS    → brew install ffmpeg")
    print("     Linux    → sudo apt install ffmpeg")
    return False


# ---------------------------------------------------------------------------
# Lazy-load heavy models so the server starts fast
# ---------------------------------------------------------------------------
_whisper_model = None


def get_whisper_model():
    """Load Whisper model once (uses 'base' for speed; change to 'small'/'medium' for accuracy)."""
    global _whisper_model
    if _whisper_model is None:
        import whisper
        print("⏳ Loading Whisper model (first time may take a minute)...")
        _whisper_model = whisper.load_model("base")
        print("✅ Whisper model loaded!")
    return _whisper_model


def translate_to_santali(text: str) -> str:
    """
    Translate English text to Santali (Ol Chiki script) using Google Translate.
    Google Translate supports Santali with language code 'sat'.
    Uses the unofficial Google Translate web API directly since the
    deep-translator library hasn't added Santali to its list yet.
    """
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",       # source language: English
        "tl": "sat",      # target language: Santali
        "dt": "t",        # return translation
        "q": text,
    }
    resp = http_requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    # Response format: [[["translated text","source text",...],...],...]
    translated = "".join(segment[0] for segment in data[0] if segment[0])
    return translated


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/transcribe", methods=["POST"])
def transcribe():
    """
    Receive audio blob from the browser, transcribe with Whisper,
    translate to Santali, and return both texts.
    """
    print("\n📥 /transcribe called")
    print(f"   Content-Type: {request.content_type}")
    print(f"   Files keys:   {list(request.files.keys())}")

    if "audio" not in request.files:
        print("   ❌ No 'audio' key in request.files")
        return jsonify({"error": "No audio file received"}), 400

    audio_file = request.files["audio"]
    print(f"   Filename: {audio_file.filename}, MIME: {audio_file.content_type}")

    # Save the uploaded audio to a temp file
    tmp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    tmp_wav   = None
    try:
        audio_file.save(tmp_input.name)
        tmp_input.close()
        file_size = os.path.getsize(tmp_input.name)
        print(f"   Saved temp file: {tmp_input.name} ({file_size} bytes)")

        if file_size < 100:
            return jsonify({"error": "Audio file is too small / empty. Please speak and try again."}), 400

        # --- Convert to WAV with ffmpeg (most reliable for Whisper) ---
        tmp_wav = tmp_input.name.replace(".webm", ".wav")
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", tmp_input.name,
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", tmp_wav
        ]
        print(f"   Converting to WAV: {' '.join(ffmpeg_cmd)}")
        proc = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            print(f"   ❌ ffmpeg error: {proc.stderr}")
            # Fallback: try using the original file directly
            tmp_wav = tmp_input.name
            print("   ⚠️  Falling back to original file")
        else:
            print(f"   ✅ WAV created: {tmp_wav} ({os.path.getsize(tmp_wav)} bytes)")

        # --- Step 1: Speech-to-Text (Whisper) ---
        print("   🔄 Running Whisper...")
        model = get_whisper_model()
        result = model.transcribe(tmp_wav, language="en", fp16=False)
        english_text = result["text"].strip()
        print(f"   📝 Whisper result: '{english_text}'")

        if not english_text:
            return jsonify({"error": "Could not recognise any speech. Please try again."}), 400

        # --- Step 2: Translate English → Santali (Ol Chiki) ---
        print("   🔄 Translating to Santali...")
        santali_text = translate_to_santali(english_text)
        print(f"   ✅ Santali: '{santali_text}'")

        return jsonify({
            "english": english_text,
            "santali": santali_text,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temp files
        try:
            os.unlink(tmp_input.name)
        except OSError:
            pass
        if tmp_wav and tmp_wav != tmp_input.name:
            try:
                os.unlink(tmp_wav)
            except OSError:
                pass


@app.route("/translate", methods=["POST"])
def translate_text():
    """
    Translate typed English text to Santali (Ol Chiki).
    Useful when the user prefers typing over speaking.
    """
    data = request.get_json(force=True)
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        santali_text = translate_to_santali(text)
        return jsonify({
            "english": text,
            "santali": santali_text,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n🚀  English → Santali (Ol Chiki) Translator")
    print("="*50)

    # Pre-flight checks
    if not check_ffmpeg():
        print("\n⚠️  The app will start but mic transcription WILL FAIL without ffmpeg.")
        print("   Text translation will still work.\n")

    # Pre-load Whisper model so first mic request isn't slow
    print("\n🔧 Pre-loading Whisper model (so first request is fast)...")
    get_whisper_model()

    print(f"\n🌐 Open http://127.0.0.1:5000 in Chrome or Edge\n")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
