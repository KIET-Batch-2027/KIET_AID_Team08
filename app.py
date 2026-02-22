"""
English to Santali (Ol Chiki) Translator
=========================================
- Takes English voice input from microphone (via browser)
- Converts English speech to text using OpenAI Whisper
- Translates English text to Santali (Ol Chiki script)
- Returns Santali text + English pronunciation (transliteration)
"""

import os
import shutil
import subprocess
import tempfile
import traceback
import warnings
import requests as http_requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Suppress warnings
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload


# ---------------------------------------------------------------------------
# Ol Chiki → Latin Transliteration
# ---------------------------------------------------------------------------
OL_CHIKI_MAP = {
    # Vowels / vowel signs
    "\u1c5a": "o",    # ᱚ
    "\u1c5b": "a",    # ᱛ  — actually ta, handled below
    "\u1c63": "i",    # ᱣ  — wi
    "\u1c64": "i",    # ᱤ
    "\u1c65": "u",    # ᱥ  — sa, handled below
    "\u1c66": "u",    # ᱦ  — ha, handled below
    "\u1c6a": "e",    # ᱪ  — ca, handled below
    "\u1c6b": "ee",   # ᱫ  — da, handled below
    "\u1c6e": "a",    # ᱮ
    "\u1c6f": "aw",   # ᱯ  — pa, handled below
    "\u1c70": "o",    # ᱰ  — dda, handled below
    "\u1c71": "oe",   # ᱱ  — na, handled below
    "\u1c72": "ah",   # ᱲ  — rra
    # Consonants (main Ol Chiki letters)
    "\u1c5b": "t",    # ᱛ
    "\u1c5c": "g",    # ᱜ
    "\u1c5d": "ng",   # ᱝ
    "\u1c5e": "l",    # ᱞ
    "\u1c5f": "m",    # ᱟ  — actually 'a' vowel
    "\u1c60": "k",    # ᱠ
    "\u1c61": "h",    # ᱡ  — ja
    "\u1c62": "ny",   # ᱢ  — ma, handled below
    "\u1c63": "w",    # ᱣ
    "\u1c66": "h",    # ᱦ
    "\u1c67": "k",    # ᱧ  — nya
    "\u1c68": "y",    # ᱨ  — ra
    "\u1c69": "r",    # ᱩ  — u
    "\u1c6a": "ch",   # ᱪ
    "\u1c6b": "d",    # ᱫ
    "\u1c6c": "j",    # ᱬ  — ttdd
    "\u1c6d": "b",    # ᱭ  — ya
    "\u1c6f": "p",    # ᱯ
    "\u1c70": "dd",   # ᱰ
    "\u1c71": "n",    # ᱱ
    "\u1c72": "rr",   # ᱲ
    "\u1c73": "s",    # ᱳ  — o long
    # Special / common
    "\u1c74": "oy",   # ᱴ  — tt
    "\u1c75": "ng",   # ᱵ
    "\u1c76": "nn",   # ᱶ
    "\u1c78": "mu",   # ᱸ  — nasal
    "\u1c79": "ha",   # ᱹ  — aha mark
    "\u1c7a": "ir",   # ᱺ
    "\u1c7b": "phat", # ᱻ
    "\u1c7c": "ahad", # ᱼ
}

# More accurate character-level Ol Chiki → Latin mapping
_OL_CHIKI_TRANSLIT = {
    # Vowels
    "\u1c5a": "o",     # ᱚ  - la
    "\u1c64": "i",     # ᱤ  - li
    "\u1c69": "u",     # ᱩ  - lu
    "\u1c6e": "e",     # ᱮ  - le
    "\u1c5f": "a",     # ᱟ  - la (a)
    "\u1c73": "o",     # ᱳ  - oo
    "\u1c74": "ow",    # ᱴ
    # Consonants
    "\u1c60": "k",     # ᱠ
    "\u1c61": "j",     # ᱡ
    "\u1c5c": "g",     # ᱜ
    "\u1c5d": "ng",    # ᱝ
    "\u1c6a": "ch",    # ᱪ
    "\u1c6c": "chh",   # ᱬ
    "\u1c5b": "t",     # ᱛ
    "\u1c6b": "d",     # ᱫ
    "\u1c70": "dd",    # ᱰ
    "\u1c71": "n",     # ᱱ
    "\u1c6f": "p",     # ᱯ
    "\u1c6d": "b",     # ᱭ  - but often 'y'
    "\u1c62": "m",     # ᱢ
    "\u1c68": "r",     # ᱨ
    "\u1c5e": "l",     # ᱞ
    "\u1c63": "w",     # ᱣ
    "\u1c65": "s",     # ᱥ
    "\u1c66": "h",     # ᱦ
    "\u1c67": "ny",    # ᱧ
    "\u1c6d": "y",     # ᱭ
    "\u1c72": "rr",    # ᱲ
    "\u1c75": "b",     # ᱵ
    "\u1c76": "v",     # ᱶ
    # Diacritics / marks
    "\u1c78": "n",     # ᱸ  - nasalisation (mu ttuddaag)
    "\u1c79": "'",     # ᱹ  - gaahlaa ttuddaag
    "\u1c7a": "",      # ᱺ  - relaa
    "\u1c7b": "",      # ᱻ  - phaarkaa
    "\u1c7c": "",      # ᱼ  - ahad
    "\u1c7d": "",      # ᱽ
    # Punctuation
    "\u1c7e": ".",     # ᱾  - mucaad
    "\u1c7f": "..",    # ᱿  - double mucaad
}


def transliterate_ol_chiki(text: str) -> str:
    """Convert Ol Chiki script text to approximate Latin / English pronunciation."""
    result = []
    for ch in text:
        if ch in _OL_CHIKI_TRANSLIT:
            result.append(_OL_CHIKI_TRANSLIT[ch])
        elif "\u1c50" <= ch <= "\u1c59":
            # Ol Chiki digits 0-9 → keep as western digits
            result.append(str(ord(ch) - 0x1C50))
        else:
            result.append(ch)        # spaces, punctuation, etc.

    raw = "".join(result)

    # Capitalise first letter of each word for readability
    return " ".join(w.capitalize() if w.isascii() else w for w in raw.split())


# ---------------------------------------------------------------------------
# FFmpeg check
# ---------------------------------------------------------------------------
def check_ffmpeg():
    if shutil.which("ffmpeg"):
        print("[OK] ffmpeg found:", shutil.which("ffmpeg"))
        return True
    print("[ERROR] ffmpeg NOT found - mic transcription will fail.")
    return False


# ---------------------------------------------------------------------------
# Whisper model (lazy-loaded)
# ---------------------------------------------------------------------------
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        print("[*] Loading Whisper model...")
        _whisper_model = whisper.load_model("base")
        print("[OK] Whisper model loaded!")
    return _whisper_model


# ---------------------------------------------------------------------------
# Google Translate (English → Santali)
# ---------------------------------------------------------------------------
def translate_to_santali(text: str) -> str:
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": "sat",
        "dt": "t",
        "q": text,
    }
    resp = http_requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return "".join(seg[0] for seg in data[0] if seg[0])


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/transcribe", methods=["POST"])
def transcribe():
    """Receive audio blob → Whisper → translate → return English + Santali + pronunciation."""
    print("\n[>] /transcribe called")

    if "audio" not in request.files:
        return jsonify({"error": "No audio file received"}), 400

    audio_file = request.files["audio"]
    tmp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    tmp_wav = None
    try:
        audio_file.save(tmp_input.name)
        tmp_input.close()
        file_size = os.path.getsize(tmp_input.name)
        print(f"   Saved: {tmp_input.name} ({file_size} bytes)")

        if file_size < 100:
            return jsonify({"error": "Audio too small. Please speak and try again."}), 400

        # Convert to WAV
        tmp_wav = tmp_input.name.replace(".webm", ".wav")
        proc = subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_input.name,
             "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", tmp_wav],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            tmp_wav = tmp_input.name  # fallback

        # Whisper
        model = get_whisper_model()
        result = model.transcribe(tmp_wav, language="en", fp16=False)
        english_text = result["text"].strip()
        if not english_text:
            return jsonify({"error": "Could not recognise speech. Please try again."}), 400

        # Translate
        santali_text = translate_to_santali(english_text)
        pronunciation = transliterate_ol_chiki(santali_text)

        print(f"   EN: {english_text}")
        print(f"   SA: {santali_text}")
        print(f"   PR: {pronunciation}")

        return jsonify({
            "english": english_text,
            "santali": santali_text,
            "pronunciation": pronunciation,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        try: os.unlink(tmp_input.name)
        except OSError: pass
        if tmp_wav and tmp_wav != tmp_input.name:
            try: os.unlink(tmp_wav)
            except OSError: pass


@app.route("/translate", methods=["POST"])
def translate_text():
    """Translate typed English text → Santali + pronunciation."""
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        santali_text = translate_to_santali(text)
        pronunciation = transliterate_ol_chiki(santali_text)
        return jsonify({
            "english": text,
            "santali": santali_text,
            "pronunciation": pronunciation,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n[*] English -> Santali (Ol Chiki) Translator")
    print("=" * 50)
    check_ffmpeg()
    print("\n[*] Pre-loading Whisper model...")
    get_whisper_model()
    print("\n[*] Open http://127.0.0.1:5000 in Chrome or Edge\n")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
