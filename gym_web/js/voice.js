const voice = {
  lastMsg: "",
  lastTime: 0,
  cooldown: 3000,
  currentSource: null, // "coach" while an Ask Coach reply is playing, else null
  speak(text, priority = false, source = "form") {
    if (this.micActive) return;
    try {
      const now = Date.now();
      if (!priority && text === this.lastMsg && (now - this.lastTime) < this.cooldown) return;
      if (!priority && (now - this.lastTime) < 800) return;
      if (!window.speechSynthesis) return;
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.rate = 1.05;
      u.onstart = () => { this.currentSource = source; };
      u.onend = () => { if (this.currentSource === source) this.currentSource = null; };
      window.speechSynthesis.speak(u);
      this.lastMsg = text;
      this.lastTime = now;
    } 
    catch (e) {
      console.warn("TTS failed", e);
    }
  }
};