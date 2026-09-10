# Gym Vision Agent — Setup Guide

## Project Structure

```
gym_vision_agent/          ← project root
├── .env.example           ← copy to .env and fill in your API key
├── .venv/                 ← Python virtual environment (Python 3.12)
├── requirements.txt       ← ALL dependencies (both sub-systems)
│
├── gym_vision_agent/      ← desktop agent package
│   ├── main.py            ← entry point for the desktop app
│   ├── core/              ← pose, engine, UI, voice
│   └── exercises/         ← 18 exercise definitions
│
├── app.py                 ← FastAPI "Ask Coach" Gemini backend
├── gym_web/               ← browser (JS/HTML) prototype
│   └── prototype.html     ← self-contained browser agent (no install needed)
└── SETUP.md               ← this file
```

---

## 1. Prerequisites

- **Python 3.12** (already installed at `C:\Users\hp\AppData\Local\Programs\Python\Python312`)
- A **Gemini API key** — get one at https://aistudio.google.com/

---

## 2. First-time setup

```powershell
# 1. Activate the virtual environment
.venv\Scripts\Activate.ps1

# 2. Install all dependencies (desktop agent + FastAPI backend)
pip install -r requirements.txt

# 3. Create your .env from the example
Copy-Item .env.example .env
# Then open .env and replace your_gemini_api_key_here with your real key
```

---

## 3. Running the Desktop Agent

The desktop agent uses your webcam (or a phone IP-camera stream) and runs entirely offline — no API key needed for pose detection.

```powershell
# Activate venv first (if not already)
.venv\Scripts\Activate.ps1

# Run from the project root
python gym_vision_agent/main.py
```

**Controls:**
| Key | Action |
|-----|--------|
| W / S | Navigate menu |
| ENTER | Confirm selection |
| A / D | Decrease / increase reps |
| SPACE | Pause / resume workout |
| Q / ESC | Quit / back to menu |

---

## 4. Running the FastAPI "Ask Coach" Backend

The backend exposes a `/ask-coach` endpoint that the browser prototype calls for AI voice answers. Requires a `.env` file with your Gemini key.

```powershell
# Activate venv first
.venv\Scripts\Activate.ps1

# Start the server (auto-reloads on code change)
uvicorn app:app --reload --port 8000
```

Test it's alive:
```powershell
Invoke-WebRequest http://localhost:8000/health
```

---

## 5. Running the Browser Prototype

The browser prototype (`gym_web/prototype.html`) is a **self-contained single HTML file** — no install needed for the browser itself. MediaPipe loads from CDN.

```powershell
# Serve locally (venv activated)
python -m http.server 8080 --directory gym_web

# Then open in Chrome on your phone or desktop:
# http://<your-laptop-ip>:8080/prototype.html
```

> **Chrome camera permission on LAN:** Go to `chrome://flags`, search for  
> "Insecure origins treated as secure", add `http://<laptop-ip>:8080`, relaunch Chrome.

---

## 6. Phone Camera (Path A — IP Webcam relay)

1. Install **IP Webcam** (Android) on your phone
2. Start the server in the app, note the IPv4 address shown (e.g. `192.168.1.5:8080`)
3. In `gym_vision_agent/main.py`, change:
   ```python
   CAMERA_INDEX = 0            # local webcam
   # to:
   CAMERA_INDEX = "http://192.168.1.5:8080/video"   # phone stream
   ```
4. Run `python gym_vision_agent/main.py`
