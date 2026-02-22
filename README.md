# 🎙️ English → Santali (Ol Chiki) Translator

A web app that **listens to your English speech**, transcribes it with **OpenAI Whisper**, translates it to **Santali** and displays the result in **Ol Chiki (ᱚᱞ ᱪᱤᱠᱤ)** script.

---

## Features

| Feature | Detail |
|---------|--------|
| 🎤 Voice input | Record from your browser microphone |
| 🗣️ Speech-to-text | OpenAI Whisper (`base` model) |
| 🌐 Translation | Google Translate (English → Santali) |
| ᱚᱞ Display | Santali shown in **Ol Chiki script** |
| ⌨️ Text input | You can also type English text directly |
| 📜 History | All translations are saved in-session |

---

## Prerequisites

1. **Python 3.9+** — [Download](https://www.python.org/downloads/)
2. **FFmpeg** — required by Whisper for audio processing
   - **Windows:** Download from https://ffmpeg.org/download.html and add to PATH
   - **Or** install via Chocolatey: `choco install ffmpeg`

---

## Quick Start

```bash
# 1. Navigate to the project folder
cd "english to santali"

# 2. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Then open **http://127.0.0.1:5000** in Chrome or Edge.

---

## How to Use

1. **Click the 🎤 mic button** and speak in English
2. Click again to **stop recording**
3. Wait a few seconds — Whisper will transcribe your speech
4. The **English text** and **Santali (Ol Chiki) translation** will appear below
5. You can also **type English text** and click **Translate**

---

## Project Structure

```
english to santali/
├── app.py                 # Flask backend (Whisper + Translation)
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── templates/
    └── index.html         # Frontend (mic + display)
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Mic not working | Use Chrome/Edge, allow mic permission |
| `ffmpeg not found` | Install FFmpeg and add to system PATH |
| Slow first run | Whisper downloads the model on first use (~140 MB) |
| Translation fails | Check your internet connection (Google Translate needs it) |

---

## Tech Stack

- **Backend:** Python, Flask
- **Speech-to-Text:** OpenAI Whisper
- **Translation:** Google Translate via `deep-translator`
- **Frontend:** Vanilla HTML/CSS/JS, Web Audio API
