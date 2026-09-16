import { t, pickVoice, getLang } from "./i18n.js"; // adjust path if inline

const voice = {
  lastMsg: "",
  lastTime: 0,
  cooldown: 3000,
  currentSource: null,
  speak(text, priority = false, source = "form") {
  if (this.micActive) return;
  // Do not let form cues interrupt an in-progress coach reply
  if (source !== "coach" && this.currentSource === "coach") return;
  const localized = t(text);
  try {
    const now = Date.now();
    if (!priority && localized === this.lastMsg && (now - this.lastTime) < this.cooldown) return;
    if (!priority && (now - this.lastTime) < 800) return;
    if (!window.speechSynthesis) return;
    // Only cancel when this utterance is allowed to speak
    window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(localized);
      u.lang = getLang() === "hi" ? "hi-IN" : "en-US";
      const v = pickVoice();
      if (v) u.voice = v;
      u.rate = 1.05;
      u.onstart = () => { this.currentSource = source; };
      u.onend = () => { if (this.currentSource === source) this.currentSource = null; };
      window.speechSynthesis.speak(u);
      this.lastMsg = localized;
      this.lastTime = now;
    } catch (e) { console.warn("TTS failed", e); }
  }
};