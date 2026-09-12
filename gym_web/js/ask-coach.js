// Layer 3 client — push-to-talk, Whisper-based STT.
//
// WHY Whisper instead of Web Speech API:
//   Web Speech API requires a SECURE origin (HTTPS or localhost).
//   When you serve the prototype over plain http://192.168.x.x on LAN,
//   Chrome on Android silently refuses to start recognition — the mic turns red
//   but onresult never fires. Whisper runs on the laptop server-side, so the
//   phone just sends a short audio blob over HTTP — no HTTPS needed.
//
// Flow:
//   Hold mic → MediaRecorder captures audio
//   Release mic → send blob to POST /transcribe (Whisper on laptop)
//   Get {text} back → show bubble + send to POST /ask-coach (Gemini)
//   Get {reply} back → show bubble + speak via TTS

// ── Config ────────────────────────────────────────────────────────────────────
// Your laptop's LAN IP — the phone POSTs here.
// Update this whenever your laptop's IP changes (or set it in one place below).
const BACKEND_URL = "http://192.168.29.196:8000";
const ASK_COACH_URL  = `${BACKEND_URL}/ask-coach`;
const TRANSCRIBE_URL = `${BACKEND_URL}/transcribe`;
const REQUEST_TIMEOUT_MS = 120000;
const FALLBACK_REPLY = "Sorry, I couldn't reach the coach just now — keep going!";

// ── Globals ───────────────────────────────────────────────────────────────────
let mediaRecorder = null;
let audioChunks   = [];
let recording     = false;

// ── UI helpers ────────────────────────────────────────────────────────────────
function showBubble(text, cls) {
  const panel = document.getElementById("coachPanel");
  if (!panel) return;
  panel.classList.add("show");
  const b = document.createElement("div");
  b.className = "coachBubble " + cls;
  b.textContent = text;
  panel.appendChild(b);
  // Keep at most 5 bubbles visible; trim oldest
  while (panel.children.length > 6) panel.removeChild(panel.firstChild);
  // Auto-scroll to newest
  panel.scrollTop = panel.scrollHeight;
}

function setStatus(text) {
  const panel = document.getElementById("coachPanel");
  if (!panel) return;
  panel.classList.add("show");
  let status = panel.querySelector(".coachBubble.status");
  if (!status) {
    status = document.createElement("div");
    status.className = "coachBubble status";
    panel.appendChild(status);
  }
  status.textContent = text;
}

function setMicVisual(state) {
  // state: "idle" | "listening" | "thinking"
  const btn = document.getElementById("micBtn");
  if (!btn) return;
  btn.classList.remove("mic-listening", "mic-thinking");
  if (state === "listening") btn.classList.add("mic-listening");
  if (state === "thinking")  btn.classList.add("mic-thinking");
}

// ── Core: send transcript to Gemini coach ────────────────────────────────────
async function sendToCoach(transcript) {
  const snapshot = window.buildSessionSnapshot ? window.buildSessionSnapshot() : null;
  if (!snapshot) return FALLBACK_REPLY;
  if (!navigator.onLine) return FALLBACK_REPLY;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(ASK_COACH_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript, session_snapshot: snapshot }),
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!res.ok) {
      console.warn("[ask-coach] server error", res.status, await res.text());
      return FALLBACK_REPLY;
    }
    const data = await res.json();
    return data.reply || FALLBACK_REPLY;
  } catch (e) {
    clearTimeout(timer);
    console.warn("[ask-coach] fetch failed:", e);
    return FALLBACK_REPLY;
  }
}

// ── Core: send audio blob to Whisper on laptop ────────────────────────────────
async function transcribeBlob(blob) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const fd = new FormData();
    fd.append("audio", blob, "recording.webm");
    const res = await fetch(TRANSCRIBE_URL, {
      method: "POST",
      body: fd,
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!res.ok) {
      console.warn("[transcribe] server error", res.status);
      return "";
    }
    const data = await res.json();
    return (data.text || "").trim();
  } catch (e) {
    clearTimeout(timer);
    console.warn("[transcribe] fetch failed:", e);
    return "";
  }
}

// ── MediaRecorder helpers ─────────────────────────────────────────────────────
async function startRecording() {
  try {
    // Only request audio — do NOT request video, we already have the camera stream
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });

    // Pick the best supported MIME type for the phone
    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "audio/ogg";

    mediaRecorder = new MediaRecorder(stream, { mimeType });
    audioChunks   = [];
    mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) audioChunks.push(e.data);
    };
    mediaRecorder.start(200); // collect chunks every 200 ms for timesliced recording
    recording = true;
  } catch (e) {
    console.warn("[mic] getUserMedia failed:", e);
    setStatus("Mic error: " + (e.message || e.name));
    recording = false;
    setMicVisual("idle");
  }
}

function stopRecording() {
  return new Promise((resolve) => {
    if (!mediaRecorder || mediaRecorder.state === "inactive") {
      resolve(null);
      return;
    }
    mediaRecorder.onstop = () => {
      const mimeType = mediaRecorder.mimeType || "audio/webm";
      const blob = new Blob(audioChunks, { type: mimeType });
      // Stop all tracks so the mic indicator light goes off
      mediaRecorder.stream.getTracks().forEach(t => t.stop());
      resolve(blob);
    };
    mediaRecorder.stop();
    recording = false;
  });
}

// ── Public init function, called from prototype.html ─────────────────────────
export function initAskCoach() {
  const btn = document.getElementById("micBtn");
  if (!btn) return;

  // Check that MediaRecorder is available (it always is in Chrome/Android)
  if (typeof MediaRecorder === "undefined") {
    btn.disabled = true;
    btn.title = "Audio recording not supported in this browser";
    return;
  }

  const start = async (e) => {
    e.preventDefault();
    if (recording) return;

    // Cancel any in-progress TTS before opening mic — prevents coach voice
    // from being picked up and re-transcribed (Section 46, gap #3)
    window.speechSynthesis && window.speechSynthesis.cancel();
    if (window.voice) window.voice.micActive = true;

    setMicVisual("listening");
    setStatus("Listening…");
    await startRecording();
  };

  const stop = async (e) => {
    e.preventDefault();
    if (!recording) return;

    setMicVisual("thinking");
    setStatus("Transcribing…");

    const blob = await stopRecording();
    if (!blob || blob.size < 1000) {
      // Too short — probably just a tap with no speech
      if (window.voice) window.voice.micActive = false;
      setStatus("Didn't catch anything — hold and speak.");
      setMicVisual("idle");
      return;
    }

    // Step 1: transcribe
    const transcript = await transcribeBlob(blob);
    if (!transcript) {
      if (window.voice) window.voice.micActive = false;
      setStatus("Couldn't hear you — try again.");
      setMicVisual("idle");
      return;
    }

    // Step 2: show what you said
    showBubble(transcript, "you");
    setStatus("Thinking…");
    if (window.voice) window.voice.micActive = false;

    // Step 3: ask Gemini
    const reply = await sendToCoach(transcript);

    // Step 4: show reply + speak it
    showBubble(reply, "coach");
    if (window.voice) {
      window.voice.speak(reply, true, "coach"); // priority=true cuts any form cue
    }
    setMicVisual("idle");
    setStatus("");
  };

  // Touch (phone) + mouse (desktop testing)
  btn.addEventListener("touchstart", start, { passive: false });
  btn.addEventListener("mousedown",  start);
  btn.addEventListener("touchend",   stop,  { passive: false });
  btn.addEventListener("mouseup",    stop);
}