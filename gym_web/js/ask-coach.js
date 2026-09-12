// Layer 3 client — push-to-talk only (Section 46, item 2: no wake word for v1).
// Two STT paths, auto-selected at runtime:
//   - Inside the RN WebView (Section 50): window.ReactNativeWebView exists,
//     so mic press/release just posts a start/stop message out to native
//     react-native-voice; the transcript comes back in via the injected
//     'message' event.
//   - Plain browser (this prototype's own testing): Web Speech API.
// sendToCoach()/the snapshot shape are identical either way — only how the
// transcript is obtained differs.

const ASK_COACH_URL = "http://192.168.29.196:8000/ask-coach"; // update once deployed (Section 59 item 7)
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
  rec.interimResults = true; // lets the status line show partial speech live
  return rec;
}

function showBubble(text, cls) {
  const panel = document.getElementById("coachPanel");
  if (!panel) return;
  panel.classList.add("show");
  const b = document.createElement("div");
  b.className = "coachBubble " + cls;
  b.textContent = text;
  panel.appendChild(b);
  while (panel.children.length > 5) panel.removeChild(panel.firstChild);
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
    showBubble(payload.transcript, "you");
    setStatus("Thinking…");
    const reply = await sendToCoach(payload.transcript);
    showBubble(reply, "coach");
    window.voice.speak(reply, false, "coach");
    setMicVisual("idle");
  });

  const start = (e) => {
    e.preventDefault();
    if (listening) return;
    // Gap #3 (Section 46): always cancel any playing TTS BEFORE opening the
    // mic — this ordering alone is what prevents the coach's own voice from
    // being re-transcribed as if the member said it.
    window.speechSynthesis.cancel();
    window.voice.micActive = true;

    if (inNativeWebView()) {
      listening = true;
      setMicVisual("listening");
      window.ReactNativeWebView.postMessage(JSON.stringify({ type: "startSTT" }));
      return;
    }

    recognition = initRecognition();
    listening = true;
    setMicVisual("listening");
    setStatus("Listening…");

    recognition.onresult = async (event) => {
      const last = event.results[event.results.length - 1];
      const transcript = last[0].transcript;

      if (!last.isFinal) {
        // Partial result — just update the live status line, don't send yet.
        setStatus(`"${transcript}"`);
        return;
      }

      // Final result — this is the one we actually act on.
      window.voice.micActive = false;
      setMicVisual("thinking");
      showBubble(transcript, "you");
      setStatus("Thinking…");
      const reply = await sendToCoach(transcript);
      showBubble(reply, "coach");
      window.voice.speak(reply, false, "coach");
      setMicVisual("idle");
    };

    recognition.onerror = (event) => {
      window.voice.micActive = false;
      setMicVisual("idle");
      listening = false;
      const messages = {
        "no-speech": "Didn't catch that — hold the mic and speak, then release.",
        "not-allowed": "Microphone is blocked — check site permissions.",
        "network": "No connection — check your phone's data or WiFi.",
      };
      setStatus(messages[event.error] || "Mic error — try again.");
    };

    recognition.onend = () => {
      window.voice.micActive = false;
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