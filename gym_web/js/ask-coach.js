// Layer 3 client — push-to-talk only (Section 46, item 2: no wake word for v1).
// Two STT paths, auto-selected at runtime:
//   - Inside the RN WebView (Section 50): window.ReactNativeWebView exists,
//     so mic press/release just posts a start/stop message out to native
//     react-native-voice; the transcript comes back in via the injected
//     'message' event.
//   - Plain browser (this prototype's own testing): Web Speech API.
// sendToCoach()/the snapshot shape are identical either way — only how the
// transcript is obtained differs.// below this line (snapshot building, fetch, fallback) is unchanged either way.

const ASK_COACH_URL = "http://localhost:8000/ask-coach"; // update once deployed (Section 59 item 7)
const REQUEST_TIMEOUT_MS = 5000;
const FALLBACK_REPLY = "Sorry, I couldn't reach the coach just now — keep going, I'll catch up.";

const inNativeWebView = () => !!window.ReactNativeWebView;


let recognition = null;
let listening = false;

function supportsSTT() {
  return inNativeWebView() || "webkitSpeechRecognition" in window || "SpeechRecognition" in window;
}

function initRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new SR();
  rec.lang = "en-US";
  rec.continuous = false;
  rec.interimResults = false;
  return rec;
}

async function sendToCoach(transcript) {
  // buildSessionSnapshot() is defined in prototype.html — the one place
  // that actually holds phase/ex/repCount/etc. This file never reaches
  // into those closures directly.
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
    if (!res.ok) return FALLBACK_REPLY;
    const data = await res.json();
    return data.reply || FALLBACK_REPLY;
  } catch (e) {
    clearTimeout(timer);
    console.warn("[ask-coach] request failed", e);
    return FALLBACK_REPLY;
  }
}

function setMicVisual(state) {
  // state: "idle" | "listening" | "thinking"
  const btn = document.getElementById("micBtn");
  if (!btn) return;
  btn.classList.remove("mic-listening", "mic-thinking");
  if (state === "listening") btn.classList.add("mic-listening");
  if (state === "thinking") btn.classList.add("mic-thinking");
}

export function initAskCoach() {
  const btn = document.getElementById("micBtn");
  if (!btn) return;

  if (!supportsSTT()) {
    btn.disabled = true;
    btn.title = "Voice Q&A isn't supported in this browser";
    return;
  }

// Native path: RN sends the finished transcript back as
// {type: "sttResult", transcript: "..."} via the WebView's injected
// message channel. This listener is a no-op in plain-browser testing
// since RN never posts these messages there.
  window.addEventListener("message", async (event) => {
    let payload;
    try { payload = JSON.parse(event.data); } catch { return; }
    if (payload?.type !== "sttResult" || !payload.transcript) return;
    setMicVisual("thinking");
    const reply = await sendToCoach(payload.transcript);
    voice.speak(reply, false, "coach");
    setMicVisual("idle");
  });

  const start = (e) => {
    e.preventDefault();
    if (listening) return;
    // Gap #3 (Section 46): always cancel any playing TTS BEFORE opening the
    // mic — this ordering alone is what prevents the coach's own voice from
    // being re-transcribed as if the member said it.
    window.speechSynthesis.cancel();

    if (inNativeWebView()) {
      listening = true;
      setMicVisual("listening");
      window.ReactNativeWebView.postMessage(JSON.stringify({ type: "startSTT" }));
      return;
    }

    recognition = initRecognition();
    listening = true;
    setMicVisual("listening");

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      setMicVisual("thinking");
      const reply = await sendToCoach(transcript);
      // Low priority + tagged "coach" — a live form correction will still
      // cut this off unconditionally (voice.js's cancel() is unconditional
      // regardless of this call's own priority flag).
      voice.speak(reply, false, "coach");
      setMicVisual("idle");
    };
    recognition.onerror = () => {
      setMicVisual("idle");
      listening = false;
    };
    recognition.onend = () => {
      listening = false;
      if (btn.classList.contains("mic-listening")) setMicVisual("idle");
    };

    recognition.start();
  };

  const stop = (e) => {
    e.preventDefault();
    if (inNativeWebView()) {
      if (listening) {
        window.ReactNativeWebView.postMessage(JSON.stringify({ type: "stopSTT" }));
        listening = false;
      }
      return;
    }
    if (recognition && listening) recognition.stop();
  };

  btn.addEventListener("mousedown", start);
  btn.addEventListener("touchstart", start, { passive: false });
  btn.addEventListener("mouseup", stop);
  btn.addEventListener("touchend", stop);
}