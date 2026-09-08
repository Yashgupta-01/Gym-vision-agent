"""
Gym Vision AI Agent — Main Entry Point
=======================================
Controls:
  MENU screen:
    ↑W / ↓S      Navigate exercises
    ENTER      Confirm selection → go to config
    Q          Quit

  CONFIG screen (reps / sets):
    A / D      Decrease / increase reps
    W / S      Decrease / increase sets
    ENTER      Start workout
    ESC        Back to menu

  WORKOUT screen:
    Q / ESC    Stop & return to menu
    SPACE      Pause / resume
"""

import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import cv2
import time
import sys
import platform
import mediapipe as mp
import threading

# Ensure the project root is in path
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.pose import PoseEstimator
from core.voice_feedback import VoiceFeedback
from core.engine import ExerciseEngine
from core.ui import (
    draw_menu, draw_reps_config, draw_calibration_screen,
    draw_workout_hud, draw_hold_hud, draw_rest_screen, draw_done_screen,
    draw_fall_alert, draw_feedback_border
)
from exercises.definitions import ALL_EXERCISES, get_exercise



class StreamReader:
    """
    Background thread that continuously reads frames from a cv2.VideoCapture
    and always exposes only the most recent one.

    Why this exists: cv2.VideoCapture buffers frames internally, and on a
    network stream (phone camera), frames arrive faster than a processing
    loop with pose estimation can drain them. cap.read() always returns the
    OLDEST queued frame, not the newest — so if the processing loop falls
    behind even slightly, the delay between real motion and what's displayed
    compounds continuously the longer the app runs (this is what caused the
    10-15s lag on the phone stream). Draining the stream on its own thread
    and keeping only the latest frame means the main loop can never fall
    behind — it just always gets "now", possibly skipping frames instead of
    queueing them.
    """

    def __init__(self, cap: cv2.VideoCapture):
        self._cap = cap
        self._lock = threading.Lock()
        self._frame = None
        self._ret = False
        self._running = True
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()

    def _reader(self):
        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                # Don't spin a tight loop hammering a dead/reconnecting stream
                time.sleep(0.02)
                continue
            with self._lock:
                self._ret = ret
                self._frame = frame

    def read(self):
        """Returns (ret, frame) — mirrors cv2.VideoCapture.read()'s signature
        so it's a drop-in replacement at call sites."""
        with self._lock:
            if self._frame is None:
                return False, None
            return self._ret, self._frame.copy()

    def isOpened(self):
        return self._cap.isOpened()

    def release(self):
        self._running = False
        self._thread.join(timeout=2)
        self._cap.release()


# PoseWorker

class PoseWorker:
    """
    Runs MediaPipe pose inference on a background thread, always processing
    the newest available frame. The main render loop reads whatever the
    latest result is instead of waiting on inference — this is what
    decouples video smoothness from pose-estimation speed. Same idea as
    StreamReader, applied to the processing step instead of the capture step.
    """

    def __init__(self, pose_estimator: PoseEstimator):
        self._pose_estimator = pose_estimator
        self._lock = threading.Lock()
        self._input_frame = None
        self._results = None
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def submit(self, frame):
        """Call every render loop iteration — cheap, just swaps a reference."""
        with self._lock:
            self._input_frame = frame

    def _worker(self):
        while self._running:
            with self._lock:
                frame = self._input_frame
                self._input_frame = None  # consume it
            if frame is None:
                time.sleep(0.005)
                continue
            results = self._pose_estimator.process(frame)
            with self._lock:
                self._results = results

    def get_latest(self):
        with self._lock:
            return self._results

    def stop(self):
        self._running = False
        self._thread.join(timeout=2)


# ─── Constants ───────────────────────────────────────────────
WINDOW_NAME = "Gym Vision AI Agent"
ANALYSIS_EVERY_N_FRAMES = 1    # only run pose + engine every N frames

CAMERA_W, CAMERA_H = 960, 540

#For --- Phone camera
# Set to a phone IP-camera stream URL (e.g. "http://192.168.1.42:8080/video")
# to use your phone as the camera instead of the laptop's built-in webcam.
# Leave as 0 to use the default local webcam.

CAMERA_INDEX = "http://192.168.29.24:8080/video"  #Replace with phone's URL or 0


# ─── App States ──────────────────────────────────────────────
APP_MENU   = "MENU"
APP_CONFIG = "CONFIG"
APP_TRAIN  = "TRAIN"

# Cached MediaPipe drawing handles (avoid re-resolving every frame)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose


def main():
    print("=" * 55)
    print("  GYM VISION AI AGENT")
    print("  18 exercises | Voice coaching | Real-time form")
    print("=" * 55)

    # ── Camera ───────────────────────────────────────────────
    is_network_stream = isinstance(CAMERA_INDEX, str)

    if is_network_stream:
        print(f"[INFO] Connecting to phone camera stream: {CAMERA_INDEX}")
        raw_cap = cv2.VideoCapture(CAMERA_INDEX)
        # Resolution/FPS are set by the phone's camera app, not controllable here —
        # calling cap.set() on a network stream is silently ignored by most backends.
        if not raw_cap.isOpened():
            print("[ERROR] Cannot open phone stream. Check that:")
            print("        - Phone and laptop are on the same WiFi network")
            print("        - The IP Webcam app is running and shows 'Start server'")
            print("        - CAMERA_INDEX matches the exact address shown on your phone")
            return
        # Wrap in StreamReader so the loop always gets the newest frame
        # instead of an ever-staler queued one.
        cap = StreamReader(raw_cap)
        time.sleep(0.3)  # give the reader thread a moment to grab a first frame
    else:
        # CAP_DSHOW is a Windows-only backend; fall back to the platform default
        # everywhere else so this actually opens the camera on macOS/Linux too.
        backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
        cap = cv2.VideoCapture(CAMERA_INDEX, backend)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAMERA_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_H)
        cap.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        print("[ERROR] Cannot open camera. Check connection.")
        return

    # ── Modules ──────────────────────────────────────────────
    print("[INFO] Loading voice engine …")
    voice = VoiceFeedback(rate=165, volume=1.0, enabled=True)

    print("[INFO] Loading pose estimator …")
    pose_estimator = PoseEstimator(model_complexity=0)
    pose_worker = PoseWorker(pose_estimator)

    engine = ExerciseEngine(voice=voice)

    # ── State ────────────────────────────────────────────────
    app_state  = APP_MENU
    ex_keys    = list(ALL_EXERCISES.keys())
    sel_idx    = 0
    target_reps = 10
    target_sets = 3
    paused     = False
    pause_started_at = None

    last_engine_state = None
    session_start_time = None
    elapsed = 0.0

    # FPS tracking
    fps_counter = 0
    fps_t = time.time()
    current_fps = 0.0

    frame_idx = 0
    last_results = None

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.waitKey(1)
    # Size the window off the camera's actual first frame rather than assuming
    # landscape — a phone stream in portrait will come back taller than wide.
    ret0, probe_frame = cap.read()
    if ret0:
        probe_h, probe_w = probe_frame.shape[:2]
        cv2.resizeWindow(WINDOW_NAME, probe_w, probe_h)
    else:
        print("[WARNING] Could not read a probe frame to size the window — using default 1280x720.")
        cv2.resizeWindow(WINDOW_NAME, 1280, 720)


    print("[INFO] Ready! Camera window is open.")
    voice.speak("Welcome to Gym Vision AI. Select your exercise.", priority=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARNING] Frame read failed, retrying …")
            time.sleep(0.05)
            continue

        frame = cv2.flip(frame, 1)   # Mirror for natural feel
        h, w = frame.shape[:2]

        # ── FPS ───────────────────────────────────────────────
        fps_counter += 1
        now = time.time()
        if now - fps_t >= 1.0:
            current_fps = fps_counter / (now - fps_t)
            fps_counter = 0
            fps_t = now

        # ── Keyboard ──────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF

        # ── MENU ─────────────────────────────────────────────
        if app_state == APP_MENU:
            pose_estimator.process(frame)   # still show skeleton preview
            draw_menu(frame, ex_keys, sel_idx)

            if key == 82 or key == ord('w'):   # UP
                sel_idx = (sel_idx - 1) % len(ex_keys)
            elif key == 84 or key == ord('s'): # DOWN
                sel_idx = (sel_idx + 1) % len(ex_keys)
            elif key == 13:                    # ENTER
                app_state = APP_CONFIG
                ex_probe = get_exercise(ex_keys[sel_idx])
                if getattr(ex_probe, "IS_DURATION_BASED", False):
                    engine.load(ex_probe, target_reps=0, target_sets=0)
                    session_start_time = time.time()
                    elapsed = 0.0
                    paused = False
                    app_state = APP_TRAIN
                else:
                    app_state = APP_CONFIG
            elif key == ord('q') or key == 27:
                break

        # ── CONFIG ────────────────────────────────────────────
        elif app_state == APP_CONFIG:
            draw_reps_config(frame, target_reps, target_sets)

            if key == ord('a'):   target_reps = max(1, target_reps - 1)
            elif key == ord('d'): target_reps = min(100, target_reps + 1)
            elif key == ord('w'): target_sets = min(20, target_sets + 1)
            elif key == ord('s'): target_sets = max(1, target_sets - 1)
            elif key == 13:       # ENTER → start
                ex_obj = get_exercise(ex_keys[sel_idx])
                engine.load(ex_obj, target_reps=target_reps, target_sets=target_sets)
                session_start_time = time.time()
                elapsed = 0.0
                paused = False
                app_state = APP_TRAIN
            elif key == 27:       # ESC → back
                app_state = APP_MENU

        # ── TRAINING ─────────────────────────────────────────
        elif app_state == APP_TRAIN:
            if key == ord('q') or key == 27:
                engine.stop()
                app_state = APP_MENU
                voice.speak("Workout stopped.", priority=True)
                continue
            if key == 32:           # SPACE → pause
                paused = not paused
                if paused:
                    pause_started_at = time.time()
                    voice.speak("Paused.", priority=True)
                else:
                    # Shift the session start forward by however long we were
                    # paused, so the paused interval isn't counted as elapsed time.
                    if session_start_time and pause_started_at:
                        session_start_time += (time.time() - pause_started_at)
                    pause_started_at = None
                    voice.speak("Resuming.", priority=True)

            if not paused:
                # Elapsed excludes both rest periods and paused time
                if session_start_time:
                    elapsed = time.time() - session_start_time
                    if last_engine_state is not None:
                        elapsed = max(0.0, elapsed - last_engine_state.total_rest_elapsed)

                timestamp = time.time()

                # Hand the newest frame to the background pose worker (non-blocking)
                pose_worker.submit(frame)

                # Draw whatever the most recently completed inference result is —
                # this may be a frame or two behind the live video during fast
                # motion, but the video itself never waits on inference.
                latest_results = pose_worker.get_latest()
                if latest_results:
                    last_results = latest_results
                if last_results and last_results.pose_landmarks:
                    mp_drawing.draw_landmarks(
                        frame,
                        last_results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style(),
                    )

                # Run engine
                if last_results and last_results.pose_landmarks:
                    lm = last_results.pose_landmarks.landmark
                    last_engine_state = engine.process_frame(lm, h, w, timestamp)
                else:
                    # No landmarks — keep last state but note no detection
                    if last_engine_state is None:
                        from core.engine import EngineState
                        last_engine_state = EngineState(phase="CALIBRATING",
                                                         display_name=ex_keys[sel_idx].replace("_", " ").title(),
                                                         message="Stand in front of camera")

                s = last_engine_state
                draw_feedback_border(frame, s.feedback_zone)

                # ── Draw appropriate overlay ──
                if s.phase == "CALIBRATING":
                    draw_calibration_screen(frame, s)
                elif s.phase == "REST":
                    draw_rest_screen(frame, s)
                elif s.phase == "DONE":
                    draw_done_screen(frame, s)
                    if key == 13:   # ENTER again → back to menu
                        app_state = APP_MENU
                elif s.phase == "FALL_ALERT":
                    draw_fall_alert(frame, s)
                    if key == 13:
                        engine.resume_after_fall()
                elif s.is_duration_based:
                    draw_hold_hud(frame, s, current_fps)
                else:
                    draw_workout_hud(frame, s, current_fps, elapsed)

                if paused:
                    # Dim the screen
                    overlay = frame.copy()
                    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
                    (tw, th), _ = cv2.getTextSize("PAUSED", cv2.FONT_HERSHEY_DUPLEX, 2, 3)
                    cv2.putText(frame, "PAUSED",
                                ((w - tw) // 2, h // 2),
                                cv2.FONT_HERSHEY_DUPLEX, 2, (0, 220, 220), 3, cv2.LINE_AA)

        cv2.imshow(WINDOW_NAME, frame)

    # ── Cleanup ───────────────────────────────────────────────
    print("[INFO] Shutting down …")
    cap.release()
    pose_worker.stop()
    pose_estimator.close()
    voice.stop()
    cv2.destroyAllWindows()
    print("[INFO] Goodbye!")


if __name__ == "__main__":
    main()
