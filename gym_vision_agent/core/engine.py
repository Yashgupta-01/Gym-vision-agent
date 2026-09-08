"""
Exercise Engine
Handles FSM state transitions, rep counting, set management, timers, 
initial posture check, and form feedback.
"""

import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from core.pose import compute_angle, get_coords, visibility, get_normalized


# ─────────────────────────────────────────────────────────────
#  Data types
# ─────────────────────────────────────────────────────────────

@dataclass
class FormError:
    message: str          # Short display text
    speech: str           # TTS text (can be more natural)
    severity: str = "warning"   # "warning" | "error"


@dataclass
class EngineState:
    """Snapshot returned to the UI every frame."""
    phase: str = "IDLE"          # IDLE | CALIBRATING | READY | WORKING | REST | DONE
    exercise_name: str = ""
    display_name: str = ""
    current_state: str = ""      # FSM state name (e.g. "down", "up")
    rep_count: int = 0
    set_count: int = 1
    target_reps: int = 10
    target_sets: int = 3
    form_errors: List[FormError] = field(default_factory=list)
    form_score: int = 100
    rest_remaining: float = 0.0   # seconds
    calibration_remaining: float = 0.0
    calibration_total: float = 2.5     # the active exercise's actual CALIBRATION_DURATION
    total_rest_elapsed: float = 0.0    # cumulative seconds spent resting so far this session
    angles: Dict[str, float] = field(default_factory=dict)
    message: str = ""             # Big centre message
    active_calibration_check: Optional[str] = None
    calibration_guide: Optional[dict] = None
    feedback_zone: str = "Red"   # Red (not visible) | Yellow (visible, in the position of performing rep) | Green (visible, correct reping position and no form errors)
    rep_rejected: bool = False    # if True, last rep was rejected due to form errors
    hold_current: float = 0.0
    hold_best: float=0.0
    is_duration_based: bool=False



@dataclass
class CalibrationCheck:
    id: str
    message: str            # spoken when this check fails
    passed_message: str     # spoken once when this check first passes
    check_fn: callable       # (landmarks, h, w) -> bool
    guide_fn: callable = None  # optional: (landmarks, h, w) -> guide overlay data
    maintain: bool= False      #  if True, this check also runs continuously during WORKING

# ─────────────────────────────────────────────────────────────
#  Base Exercise
# ─────────────────────────────────────────────────────────────

class BaseExercise:
    """
    Base class for all exercises.
    Subclasses define: angles, FSM states, feedback, and posture check.
    """

    name: str = "base"
    display_name: str = "Exercise"
    IS_DURATION_BASED: bool = False
    # Spoken correction shown/said while the user is NOT in the correct
    # starting posture during calibration. Override per exercise below.
    START_CUE: str = "Get into the starting position and hold still."
    # Minimum seconds between two counted reps (prevents double-counting)
    MIN_REP_DURATION: float = 0.7

    # Seconds in correct start pose before workout begins
    CALIBRATION_DURATION: float = 2.5

    TRACKED_LANDMARKS: List[str] = []

    def get_rep_quality_errors(self) -> Optional[FormError]:
        """
        Override alongside USES_REP_QUALITY_TRACKING = True. Return the
        worst named-tracker violation for the rep cycle that just completed
        (or None if clean), and reset the tracker(s) for the next cycle.
        Called exactly once, at the counting frame.
        """
        return None


    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all counters and state."""
        self.current_state: Optional[str] = None
        self.prev_state: Optional[str] = None
        self._last_count_time: float = 0.0
        self._current_time: float = 0.0
        self._computed_angles: Dict[str, float] = {}
        # Calibration
        self._cal_start: Optional[float] = None
        self.is_calibrated: bool = False
        # Form score
        self._rep_scores: List[int] = []
        self.current_form_score: int = 100
        self.avg_form_score: int = 100
        self._rep_had_error: bool = False
        self._rep_error_reason: Optional[FormError] = None

    # ── Override in subclass ──────────────────────────────────

    def compute_angles(self, landmarks, h: int, w: int) -> Dict[str, float]:
        """Compute and return a dict of {angle_name: degrees}."""
        return {}

    def get_fsm_state(self, angles: Dict[str, float], landmarks, h: int, w: int) -> str:
        """Return the current FSM state name based on angles."""
        return "start"

    def should_count(self) -> bool:
        """Return True when a rep should be counted (called after state update)."""
        return False

    def check_form_errors(self, angles: Dict[str, float], landmarks, h: int, w: int) -> List[FormError]:
        """Return a list of active form errors."""
        return []

    def check_start_posture(self, landmarks, h: int, w: int) -> bool:
        """Return True when the user is in a valid starting position."""
        return True

    def get_calibration_checks(self) -> List["CalibrationCheck"]:
        """Override per-exercise. Ordered list, checked top to bottom."""
        return []

    # ── Engine internals ──────────────────────────────────────

    def update(self, landmarks, h: int, w: int, timestamp: float) -> Dict[str, Any]:
        """
        Called every analysed frame.
        Returns a result dict used by ExerciseEngine.
        """
        self._current_time = timestamp
        angles = self.compute_angles(landmarks, h, w)
        self._computed_angles = angles

        new_state = self.get_fsm_state(angles, landmarks, h, w)
        self.prev_state = self.current_state
        self.current_state = new_state

        form_errors = self.check_form_errors(angles, landmarks, h, w)
        if form_errors:
            self._rep_had_error = True
            self._rep_error_reason = form_errors[0]
        score = max(0, 100 - len(form_errors) * 20)
        self.current_form_score = score

        counted = False
        rep_had_error = False
        rep_error_reason = None
        if self.should_count():
            quality_error = self.get_rep_quality_errors() if self.USES_REP_QUALITY_TRACKING else None
            dt = timestamp - self._last_count_time

            if dt >= self.MIN_REP_DURATION:
                counted = True
                self._last_count_time = timestamp
                if self.USES_REP_QUALITY_TRACKING:
                    rep_error_reason = quality_error
                    rep_had_error = quality_error is not None
                else:
                    rep_had_error = self._rep_had_error
                    rep_error_reason = self._rep_error_reason
            # Reset the accumulator for the next attempt either way — a
            # rejected-by-debounce attempt shouldn't leak its faults into
            # the next one.
            self._rep_had_error = False
            self._rep_error_reason = None

        return {
            "state": new_state,
            "counted": counted,
            "form_errors": form_errors,
            "rep_had_error": rep_had_error,
            "rep_error_reason": rep_error_reason,
            "form_score": score,
            "angles": angles,
        }


    def check_calibration(self, landmarks, h: int, w: int, timestamp: float) -> float:
        """
        Monitor calibration pose. Returns seconds held (0 if wrong pose).
        When calibration finishes, sets self.is_calibrated = True.
        """
        if self.is_calibrated:
            return self.CALIBRATION_DURATION

        if self.check_start_posture(landmarks, h, w):
            if self._cal_start is None:
                self._cal_start = timestamp
            held = timestamp - self._cal_start
            if held >= self.CALIBRATION_DURATION:
                self.is_calibrated = True
            return held
        else:
            self._cal_start = None
            return 0.0

    def get_calibration_checks(self) -> List["CalibrationCheck"]:
        """Ordered list — checked top to bottom, first failure wins."""
        return []

# ─────────────────────────────────────────────────────────────
#  Exercise Engine (manages sets / rest / voice pipeline)
# ─────────────────────────────────────────────────────────────

class ExerciseEngine:
    """High-level controller that drives one exercise session."""

    REST_DURATION = 60.0    # seconds between sets

    def __init__(self, voice=None):
        self._voice = voice
        self._exercise: Optional[BaseExercise] = None
        self._phase = "IDLE"

        self._rep_count = 0
        self._set_count = 1
        self._target_reps = 10
        self._target_sets = 3

        self._rest_start: Optional[float] = None
        self._session_start: Optional[float] = None
        self._total_rest_accum: float = 0.0   # sum of all completed rest periods this session

        # Spam-protection for voice
        self._last_spoken_error: str = ""
        self._last_error_time: float = 0.0
        self._error_cooldown: float = 6.0

        # Calibration posture-cue spam-protection + positive reinforcement tracking
        self._last_cal_cue: str = ""
        self._last_cal_cue_time: float = 0.0
        self._cal_cue_cooldown: float = 6.0
        self._cal_was_in_position: bool = False

        # Positive reinforcement tracking for working-phase form errors
        self._had_form_error: bool = False

        self._cal_failed_ids: Dict[str, bool] = {}
        self._cal_active_check_id: Optional[str] = None

        # Fall detection
        self._prev_hip_y: Optional[float] = None
        self._prev_hip_time: Optional[float] = None
        self._fall_cooldown_until: float = 0.0

        #Visibility gating
        self._was_visible = True

        self._is_duration = False
        self._hold_best = 0.0
        self._hold_seg_start = None
        


    # ── Public API ────────────────────────────────────────────

    def load(self, exercise: BaseExercise, target_reps: int = 10, target_sets: int = 3):
        """Load an exercise and start calibration phase."""
        self._exercise = exercise
        self._exercise.reset()
        self._target_reps = target_reps
        self._target_sets = target_sets
        self._rep_count = 0
        self._set_count = 1
        self._rest_start = None
        self._phase = "CALIBRATING"
        self._session_start = None
        self._total_rest_accum = 0.0
        self._cal_was_in_position = False
        self._last_cal_cue = ""
        self._had_form_error = False
        self._speak(f"Get ready for {exercise.display_name}. Hold the starting position.", priority=True)

        self._cal_failed_ids = {}
        self._cal_active_check_id = None

        self._is_duration = getattr(exercise, "IS_DURATION_BASED", False)
        self._hold_best = 0.0
        self._hold_seg_start = None


    def stop(self):
        self._phase = "IDLE"

    def process_frame(self, landmarks, h: int, w: int, timestamp: float) -> EngineState:
        """
        Main entry point — call every frame (or every N frames).
        Returns an EngineState snapshot.
        """
        state = EngineState(
            phase=self._phase,
            exercise_name=self._exercise.name if self._exercise else "",
            display_name=self._exercise.display_name if self._exercise else "",
            target_reps=self._target_reps,
            target_sets=self._target_sets,
            rep_count=self._rep_count,
            set_count=self._set_count,
        )
        insufficient_visibility = False

        if not self._exercise or not landmarks:
            return state
         # Gate everything on basic visibility BEFORE running any exercise logic —
        # this is what stops reps from counting on garbage/partial landmark data,
        # and is what drives the RED zone.

        if not self._core_visible(landmarks):
            state.feedback_zone="Red"
            state.message = "Step into frame - I can't see you clearly."
            if self._was_visible:
                self._speak("Correct your position.", priority=True)
                self._was_visible = False
            return state
        self._was_visible = True


        # ── FALL DETECTION (optional) ────────────────────────
        if timestamp >= self._fall_cooldown_until and self._phase in ("WORKING", "REST", "CALIBRATING"):
            if self._check_fall(landmarks, h, w, timestamp):
                self._phase = "FALL_ALERT"
                self._fall_cooldown_until = timestamp + 5.0
                self._speak("Whoa, are you okay? Press enter when you're ready to continue.", priority=True)
                state.phase = self._phase
                state.message = "Fall or sudden movement detected — paused."
                return state

        ex = self._exercise

        # ── CALIBRATING ──────────────────────────────────────
        if self._phase == "CALIBRATING":
            failing_check = self._run_calibration_checks(ex, landmarks, h, w, timestamp)
            state.active_calibration_check = failing_check.id if failing_check else None
            state.calibration_guide = (
                failing_check.guide_fn(landmarks, h, w)
                if failing_check and failing_check.guide_fn else None
            )

            if failing_check is None:
                held = ex.check_calibration(landmarks, h, w, timestamp)
                remaining = max(0.0, ex.CALIBRATION_DURATION - held)
                state.calibration_remaining = remaining
                state.message = f"Hold still... {remaining:.1f}s" if held > 0 else "Hold the position!"
            else:
                state.calibration_remaining = ex.CALIBRATION_DURATION
                state.message = failing_check.message

            if ex.is_calibrated:
                self._phase = "WORKING"
                self._session_start = timestamp
                self._speak(f"Go! Start your {ex.display_name}.", priority=True)

        # ── REST ─────────────────────────────────────────────
        elif self._phase == "REST":
            elapsed = timestamp - self._rest_start
            remaining = max(0.0, self.REST_DURATION - elapsed)
            state.rest_remaining = remaining

            if remaining <= 0:
                # Start next set — fold this completed rest period into the total
                self._total_rest_accum += elapsed
                state.total_rest_elapsed = self._total_rest_accum
                ex.reset()
                ex.is_calibrated = True   # Skip re-calibration between sets
                self._rep_count = 0
                self._phase = "WORKING"
                self._speak(f"Set {self._set_count}, Go!", priority=True)
            else:
                state.message = f"REST — {int(remaining)}s"
                if int(remaining) in (30, 10, 5, 3, 2, 1):
                    self._speak_once(f"{int(remaining)} seconds remaining")
                # Still resting — report accumulated total plus this in-progress period
                state.total_rest_elapsed = self._total_rest_accum + elapsed

        # ── WORKING ──────────────────────────────────────────
        elif self._phase == "WORKING":
            if not self._working_visible(ex, landmarks):
                # Don't feed low-confidence joints into this exercise's FSM at
                # all — mirrors _core_visible()'s gate, just scoped to the
                # specific joints THIS exercise's angle math depends on
                # (Section 17/29: shoulder+hip alone isn't enough for e.g.
                # Squat, which also needs knee+ankle).
                insufficient_visibility = True
                state.current_state = ex.current_state or ""
                state.message = "Keep your knees, ankles, and other tracked joints in frame."
            else:
                result = ex.update(landmarks, h, w, timestamp)
                maint_fail=self._check_maintenance(ex, landmarks, h, w)
                if maint_fail:
                    result["form_errors"]=list(result["form_errors"])+[
                        FormError(maint_fail.message, maint_fail.message, severity="warning")]
                state.current_state = result["state"]
                state.angles = result["angles"]
                state.form_errors = result["form_errors"]
                state.form_score = result["form_score"]

                if self._is_duration:
                    # Freeform hold tracking — no reps/sets, just current hold time
                    # and personal best. Uses the exercise's own "hold"/"break" FSM
                    # states (Plank and WallSit both already expose these).
                    if ex.current_state == "hold":
                        if self._hold_seg_start is None:
                            self._hold_seg_start = timestamp
                        state.hold_current = timestamp - self._hold_seg_start
                    else:
                        if self._hold_seg_start is not None:
                            achieved = timestamp - self._hold_seg_start
                            if achieved >= 3.0:
                                if achieved > self._hold_best:
                                    self._hold_best = achieved
                                    self._speak(f"New best! {achieved:.0f} seconds.", priority=True)
                                else:
                                    self._speak(f"Hold released at {achieved:.0f} seconds.", priority=False)
                            self._hold_seg_start = None
                        state.hold_current = 0.0
                    state.hold_best = self._hold_best

                # Rep counted — only if form was clean at the moment of completion.
                # A messy rep still consumes the attempt (FSM flags already reset by
                # should_count()), it just doesn't increment the counter, so the user
                # has to redo the full motion cleanly to get credit for it.
                elif result["counted"]:
                    if result["form_errors"]:
                        worst = result["rep_error_reason"] or (
                            result["form_errors"][0] if result["form_errors"] else None
                        )
                        speech = worst.speech if worst else "Fix your form and try again."
                        self._speak(f"Not counted. {speech}", priority=True)
                        state.rep_rejected = True

                    else:
                        self._rep_count += 1
                        state.rep_count = self._rep_count
                        self._speak(f"Excellent! Rep {self._rep_count}", priority=False)

                        if self._rep_count >= self._target_reps:
                            if self._set_count >= self._target_sets:
                                self._phase = "DONE"
                                self._speak("Workout complete! Great job!", priority=True)
                            else:
                                self._set_count += 1
                                self._rest_start = timestamp
                                self._phase = "REST"
                                self._speak(
                                    f"Set {self._set_count - 1} done! Rest for {int(self.REST_DURATION)} seconds.",
                                    priority=True,
                                )

                # Voice form feedback (with cooldown)
                self._handle_form_speech(result["form_errors"], timestamp)



        # ── DONE ─────────────────────────────────────────────
        elif self._phase == "DONE":
            state.message = "WORKOUT COMPLETE! Great job!"
        elif self._phase == "FALL_ALERT":
            state.message = "Paused — press ENTER when ready to continue."
        elif self._phase == "IDLE":
            state.message = "Stand ready. Say \"Let's start\" to begin."
        elif self._phase == "READY":
            state.message = "Ready... GO!"
        elif self._phase == "CALIBRATING":
            state.message = "Hold still for calibration."
        elif self._phase == "REST":
            state.message = f"Rest — {int(self.REST_DURATION)} seconds."

            
        # Finalise state
        state.rep_count = self._rep_count
        state.set_count = self._set_count
        state.phase = self._phase
        state.is_duration_based = self._is_duration

        if self._phase != "REST":
            state.total_rest_elapsed = self._total_rest_accum
        
         # Feedback zone: RED (not visible) -> YELLOW (visible, not correct yet) -> GREEN (correct)
        
        if self._phase == "CALIBRATING":
            state.feedback_zone = "YELLOW" if state.active_calibration_check else "GREEN"
        elif self._phase == "WORKING":
            state.feedback_zone = "YELLOW" if (insufficient_visibility or state.form_errors) else "GREEN"
        elif self._phase in ("REST", "DONE"):
            state.feedback_zone = "GREEN"
        else:
            state.feedback_zone = "YELLOW"

        return state

    def _core_visible(self, landmarks) -> bool:
        """Generic baseline: is enough of the torso visible to trust any reading at all.
        Exercise-specific visibility checks (full body, side profile, etc.) still run independently.
        inside get_calibration_checks() - this is just red/not red gate. So 
        """
        try:
            return (
                visibility(landmarks, "left_shoulder") > 0.4 and 
                visibility(landmarks, "right_shoulder") > 0.4 and
                visibility(landmarks, "left_hip") > 0.4 and
                visibility(landmarks, "right_hip") > 0.4
            )
        except Exception:
            return False

    # ── Internal helpers ──────────────────────────────────────
    def _working_visible(self, ex, landmarks) -> bool:
        """
        Exercise-specific visibility gate for the WORKING phase.

        _core_visible() only checks shoulder/hip — enough to know someone is
        roughly in frame, but not enough to trust the ACTIVE exercise's own
        angle math, which may depend on knees, ankles, elbows, etc. Feeding
        low-confidence versions of those specific joints into compute_angles()
        can swing the FSM across state thresholds on landmark noise alone
        (this is exactly what happened in the JS prototype — Section 29, bug #4).

        Uses an AVERAGED threshold across the declared joints, not a strict
        AND of all of them — a strict per-joint gate froze the FSM on a
        momentary confidence dip in any single joint, which is normal noise,
        not real occlusion (Section 29, bug #5).
        """
        joints = getattr(ex, "TRACKED_LANDMARKS", None)
        if not joints:
            return True  # exercise hasn't declared specific joints — core gate is sufficient
        try:
            scores = [
                max(visibility(landmarks, f"left_{joint}"), visibility(landmarks, f"right_{joint}"))
                for joint in joints
            ]
        except Exception:
            return True  # never let a missing/misnamed landmark crash the gate
        if not scores:
            return True
        return (sum(scores) / len(scores)) > 0.35



    def _handle_form_speech(self, errors: List[FormError], timestamp: float):
        if not errors:
            return
        worst = errors[0]  # Speak only the top error
        since_last = timestamp - self._last_error_time
        if worst.speech != self._last_spoken_error or since_last >= self._error_cooldown:
            self._speak(worst.speech)
            self._last_spoken_error = worst.speech
            self._last_error_time = timestamp

    def _speak(self, text: str, priority: bool = False):
        if self._voice:
            self._voice.speak(text, priority=priority)

    def _speak_once(self, text: str):
        if self._voice:
            self._voice.speak_once(text)

    def _speak_calibration_cue(self, cue: str, timestamp: float):
        """Speak a posture-correction cue, but not on every single frame."""
        since_last = timestamp - self._last_cal_cue_time
        if cue != self._last_cal_cue or since_last >= self._cal_cue_cooldown:
            self._speak(cue, priority=False)
            self._last_cal_cue = cue
            self._last_cal_cue_time = timestamp

    def _run_calibration_checks(self, ex, landmarks, h, w, timestamp):
        checks = ex.get_calibration_checks()
        if not checks:
            return None  # exercise hasn't defined checks yet -> fall back to old behavior
        for chk in checks:
            ok = chk.check_fn(landmarks, h, w)
            was_failing = self._cal_failed_ids.get(chk.id, True)
            if not ok:
                self._cal_failed_ids[chk.id] = True
                if self._cal_active_check_id != chk.id:
                    self._speak(chk.message, priority=True)
                    self._cal_active_check_id = chk.id
                else:
                    self._speak_once(chk.message)
                return chk
            else:
                if was_failing:
                    self._speak(chk.passed_message, priority=True)
                self._cal_failed_ids[chk.id] = False
        self._cal_active_check_id = None
        return None


    def _check_maintenance(self, ex, landmarks, h, w):
        """Re-run only the checks marked maintain=True, even mid-set."""
        for chk in ex.get_calibration_checks():
            if chk.maintain and not chk.check_fn(landmarks, h, w):
                return chk
        return None

    def _check_fall(self, landmarks, h, w, timestamp) -> bool:
        lh = get_coords(landmarks, "left_hip", h, w)
        rh = get_coords(landmarks, "right_hip", h, w)
        hip_y_norm = ((lh[1] + rh[1]) / 2.0) / h

        fell = False
        if self._prev_hip_y is not None and self._prev_hip_time is not None:
            dt = timestamp - self._prev_hip_time
            drop = hip_y_norm - self._prev_hip_y
            if dt > 0 and dt < 0.5 and drop > 0.35:
                fell = True
        self._prev_hip_y = hip_y_norm
        self._prev_hip_time = timestamp
        return fell

    def resume_after_fall(self):
        if self._exercise:
            self._exercise.reset()
        self._phase = "CALIBRATING"
        self._speak("Let's get back into position.", priority=True)