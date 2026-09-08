"""
Voice Feedback Module
Asynchronous Text-to-Speech using pyttsx3.
Runs in a background thread so it never blocks the video stream.
"""

import threading
import queue
import time

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("[WARNING] pyttsx3 not installed. Voice feedback disabled. Run: pip install pyttsx3")


class VoiceFeedback:
    """
    Non-blocking TTS engine.
    Messages are queued and spoken in order by a background thread.
    """

    def __init__(self, rate=160, volume=1.0, enabled=True):
        self.enabled = enabled and TTS_AVAILABLE
        self._queue = queue.Queue()
        self._engine = None
        self._thread = None
        self._last_message = ""
        self._last_message_time = 0
        self._cooldown = 3.0        # seconds between same message
        self._running = False

        if self.enabled:
            self._start_thread(rate, volume)

    # ------------------------------------------------------------------
    def _start_thread(self, rate, volume):
        """Start the background TTS thread."""
        self._running = True
        self._thread = threading.Thread(
            target=self._worker, args=(rate, volume), daemon=True
        )
        self._thread.start()

    def _worker(self, rate, volume):
        """
        Background worker.

        IMPORTANT: pyttsx3's SAPI5 (Windows) driver has a long-standing bug where
        reusing a single engine instance across repeated say()/runAndWait() calls
        works exactly once — the first message speaks fine, then the driver's
        internal run-loop state gets stuck and every subsequent call silently
        does nothing (no error, no exception, just silence). The reliable fix is
        to create a fresh engine per message instead of one long-lived engine.
        """
        try:
            while self._running:
                try:
                    message = self._queue.get(timeout=0.5)
                    if message is None:        # Shutdown signal
                        break
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty("rate", rate)
                        engine.setProperty("volume", volume)
                        voices = engine.getProperty("voices")
                        if voices:
                            engine.setProperty("voice", voices[0].id)
                        engine.say(message)
                        engine.runAndWait()
                        engine.stop()
                        del engine
                    except Exception as e:
                        print(f"[VoiceFeedback] TTS error: {e}")
                    self._queue.task_done()
                except queue.Empty:
                    continue
        except Exception as e:
            print(f"[VoiceFeedback] Engine init error: {e}")
            self.enabled = False

    # ------------------------------------------------------------------
    def speak(self, message: str, priority: bool = False):
        """
        Queue a message for speech.
        
        Args:
            message: Text to speak.
            priority: If True, bypass cooldown (for important alerts).
        """
        if not self.enabled:
            return

        now = time.time()
        is_same = message == self._last_message
        cooldown_ok = (now - self._last_message_time) >= self._cooldown

        if priority or not is_same or cooldown_ok:
            # Don't let the queue grow unboundedly – drop old coaching messages
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except queue.Empty:
                    break

            self._queue.put(message)
            self._last_message = message
            self._last_message_time = now

    def speak_once(self, message: str):
        """Speak a message only once (won't repeat until a different message)."""
        if message != self._last_message:
            self.speak(message)

    def stop(self):
        """Cleanly shut down the TTS engine."""
        self._running = False
        if self._queue:
            self._queue.put(None)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
