const voice = {
  lastMsg: "",
  lastTime: 0,
  cooldown: 3000,
  speak(text, priority = false) {
    try {
      const now = Date.now();
      if (!priority && text === this.lastMsg && (now - this.lastTime) < this.cooldown) return;
      if (!priority && (now - this.lastTime) < 800) return;
      if (!window.speechSynthesis) return;
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.rate = 1.05;
      window.speechSynthesis.speak(u);
      this.lastMsg = text;
      this.lastTime = now;
    } catch (e) {
      console.warn("TTS failed", e);
    }
  }
};