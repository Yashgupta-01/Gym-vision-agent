"""
Ask Coach — Layer 3 backend (project summary Sections 46/49)

Minimal FastAPI service: receives {transcript, session_snapshot} from the
JS coach session (prototype.html / react-native-webview), calls Gemini
with a scoped system prompt, and returns {reply}. The API key lives here,
server-side, and is NEVER shipped to the client — that's the entire reason
this service exists (Section 46, gap #1: a client-side key in a bundled
WebView asset is trivially extractable).

Run locally:
    pip install -r requirements.txt
    cp .env.example .env   # then fill in GEMINI_API_KEY
    uvicorn app:app --reload --port 8000

The JS side POSTs to /ask-coach once per push-to-talk press (Section 46,
gap #5 — snapshot is built once, not polled).
"""

import os
from typing import List, Optional

from dotenv import load_dotenv
import tempfile
import shutil

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google import genai
from google.genai import types as genai_types

load_dotenv()

# ── Config ──────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Put it in a .env file (see .env.example) "
        "or your environment — never hardcode it in source."
    )

client = genai.Client(api_key=GEMINI_API_KEY)

# Free-tier-friendly, low-latency model — good fit for short in-session
# replies spoken aloud mid-set. Override via env if you want a bigger model
# for the post-session comparison narrative later (Section 46 item 7).
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

# Section 43: gym + health + session scope only, short answers, no diagnosis.
# Section 49: this service never touches MediaPipe/landmarks/video — it only
# ever sees the small session_snapshot JSON the JS engine already computed.
SYSTEM_PROMPT = """You are "Coach", a brief in-session voice assistant for a \
gym app called Ignite. The member is mid-workout; their phone is watching \
their form via on-device computer vision — you are NOT that system and you \
never invent rep counts, angles, or form judgments. The session_snapshot \
you're given is ground truth; treat it as authoritative.

Scope — answer ONLY:
- questions about the current, previous, or next exercise in this session
- form cues, depth, tempo, rest guidance
- light, general health/food guidance

Anything outside that scope (news, relationships, coding, etc.): refuse in \
one short sentence and steer back to the workout. No lecture.

Rules:
- Never diagnose. If the member mentions pain, tell them to stop and see a \
  professional, plus at most one general form-safety tip — nothing else.
- Keep replies to 1-2 short sentences — this gets spoken aloud through TTS \
  mid-set, not read.
- Never contradict the rep count or form errors already in the \
  session_snapshot. If asked "was that rep good", answer from \
  recent_form_errors, don't guess independently.
"""

app = FastAPI(title="Ignite Ask Coach")

# CORS: reads a comma-separated ALLOWED_ORIGINS env var so the same code
# works in both states — unset/empty falls back to "*" for local dev and
# the react-native-webview bundled-asset case (Section 50: the WebView
# origin there is effectively file://, which doesn't benefit from a strict
# allowlist anyway). Once this is deployed behind a real domain and the
# WebView points at it over HTTPS (Section 59 item 7), set
# ALLOWED_ORIGINS=https://your-deployed-origin.com in the environment —
# no code change needed at that point.
_origins_env = os.environ.get("ALLOWED_ORIGINS", "").strip()
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class SessionSnapshot(BaseModel):
    exercise: str
    set: int
    reps: int
    targetReps: int
    targetSets: int
    phase: str
    recentFormErrors: List[str] = Field(default_factory=list)
    lastCue: Optional[str] = ""


class AskRequest(BaseModel):
    transcript: str
    session_snapshot: SessionSnapshot


class AskResponse(BaseModel):
    reply: str


# Always have a spoken fallback ready rather than silence or a raw error
# (Section 46, gap #6) — a phone mid-workout shouldn't ever get a 500.
FALLBACK_REPLY = "Sorry, I couldn't get an answer just now — keep going, I'll catch up."


def build_prompt(req: AskRequest) -> str:
    snap = req.session_snapshot
    return (
        f"Current session state:\n"
        f"- Exercise: {snap.exercise}\n"
        f"- Set: {snap.set}/{snap.targetSets}\n"
        f"- Reps this set: {snap.reps}/{snap.targetReps}\n"
        f"- Phase: {snap.phase}\n"
        f"- Recent form errors: {', '.join(snap.recentFormErrors) or 'none'}\n"
        f"- Last coaching cue: {snap.lastCue or 'none'}\n\n"
        f'Member just asked: "{req.transcript}"'
    )


@app.post("/ask-coach", response_model=AskResponse)
def ask_coach(req: AskRequest):
    prompt = build_prompt(req)
    try:
        chat = client.chats.create(
            model=MODEL_NAME,
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=250,
                temperature=0.4,
            )
        )
        response = chat.send_message(prompt)
        text = (response.text or "").strip()
        return AskResponse(reply=text or FALLBACK_REPLY)
    except Exception as e:
        print(f"[ask-coach] Gemini call failed: {e}")
        return AskResponse(reply=FALLBACK_REPLY)


# ── Whisper transcription endpoint ───────────────────────────────────────────
# The phone records audio with MediaRecorder (webm/ogg), POSTs it here as
# multipart/form-data, and gets back {"text": "..."}.
# This exists because Web Speech API requires HTTPS — unavailable on a plain
# LAN http://192.168.x.x URL. Whisper runs locally on the laptop, no cost.
_whisper_model = None  # lazy-loaded on first request

def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        try:
            import os
            # Force inject winget's ffmpeg into the environment PATH just in case 
            # Windows failed to update the user's terminal environment correctly.
            ffmpeg_dir = r"C:\Users\hp\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin"
            if os.path.exists(ffmpeg_dir) and ffmpeg_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] += os.pathsep + ffmpeg_dir

            import whisper
            print("[transcribe] Loading Whisper 'base' model (one-time, ~140 MB)…")
            _whisper_model = whisper.load_model("base")
            print("[transcribe] Whisper ready.")
        except ImportError:
            raise RuntimeError(
                "openai-whisper is not installed. "
                "Run: pip install openai-whisper"
            )
    return _whisper_model


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """Receive an audio blob, transcribe with Whisper, return {text}."""
    suffix = ".webm"  # Chrome/Android records as webm; ffmpeg handles it
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(audio.file, tmp)
        tmp_path = tmp.name
    try:
        model = _get_whisper()
        result = model.transcribe(tmp_path, language="en", fp16=False)
        text = result.get("text", "").strip()
        return {"text": text}
    except Exception as e:
        print(f"[transcribe] Whisper failed: {e}")
        return {"text": ""}
    finally:
        import os as _os
        _os.unlink(tmp_path)


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}