"""
All 18 Exercise Definitions
Each class extends BaseExercise and implements:
  - compute_angles()
  - get_fsm_state()
  - should_count()
  - check_form_errors()
  - check_start_posture()
  - get_calibration_checks()
"""
import math
from core.engine import BaseExercise, FormError, CalibrationCheck
from core.pose import compute_angle, get_coords, get_normalized, visibility
from typing import Dict, List, Optional

# ─────────────────────────────────────────────────────────────
#  1. SQUAT
#--------------------------------------------------------------


class Squat(BaseExercise):
    name = "squat"
    display_name = "Squat"
    START_CUE = "Stand tall with your feet shoulder-width apart."
    MIN_REP_DURATION = 1.0
    CALIBRATION_DURATION = 1.5
    TRACKED_LANDMARKS = ["hip", "knee", "ankle"]
    USES_REP_QUALITY_TRACKING = True


    def __init__(self):
        super().__init__()
        self._reached_down = False
        self._had_valgus_this_rep = False


    def reset(self):
        super().reset()
        self._reached_down = False
        self._had_valgus_this_rep = False


    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        left_knee = compute_angle(lm, "left_hip", "left_knee", "left_ankle", h, w)
        right_knee = compute_angle(lm, "right_hip", "right_knee", "right_ankle", h, w)
        
        avg_knee = (left_knee + right_knee) / 2.0

        lk = get_coords(lm, "left_knee", h, w)
        rk = get_coords(lm, "right_knee", h, w)
        la = get_coords(lm, "left_ankle", h, w)
        ra = get_coords(lm, "right_ankle", h, w)

        knee_dist = math.hypot(lk[0] - rk[0], lk[1] - rk[1])
        ankle_dist = math.hypot(la[0] - ra[0], la[1] - ra[1]) + 1e-6
        valgus_ratio = knee_dist / ankle_dist

        return {
            "left_knee": left_knee,
            "right_knee": right_knee,
            "avg_knee": avg_knee,
            "valgus_ratio": valgus_ratio
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        avg_knee = angles.get("avg_knee", 180.0)

        # Relaxed lockout threshold
        if avg_knee >= 150.0:
            return "up"
        # Relaxed depth threshold to comfortably register parallel/functional squats
        elif avg_knee <= 120.0:
            self._reached_down = True
            return "down"

        return "mid"

    def should_count(self) -> bool:
        if self.current_state == "up" and self._reached_down:
            self._reached_down = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        avg_knee = angles.get("avg_knee", 180.0)
        valgus_ratio = angles.get("valgus_ratio", 1.0)

        if self.prev_state == "up" and self.current_state != "up":
            self._had_valgus_this_rep = False
        
        # Essential check: Knees caving in significantly
        if valgus_ratio < 0.70 and avg_knee < 140.0:
            errors.append(FormError(
                message="Knees caving in",
                speech="Push your knees outward.",
                severity="warning"
            ))

        return errors

    def get_rep_quality_errors(self) -> Optional[FormError]:
        had_valgus = self._had_valgus_this_rep
        self._had_valgus_this_rep = False
        if had_valgus:
            return FormError(
                message="Knees caving in",
                speech="Push your knees outward.",
                severity="warning"
            )
        return None

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        return angles["avg_knee"] >= 145.0

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="full_body_visible_frontal",
                message="Face the camera and step back so your full body is visible.",
                passed_message="Full body detected.",
                check_fn=lambda lm, h, w: (
                    visibility(lm, "left_ankle") > 0.3 and visibility(lm, "right_ankle") > 0.3 and
                    visibility(lm, "left_shoulder") > 0.3 and visibility(lm, "right_shoulder") > 0.3
                ),
            ),
            CalibrationCheck(
                id="legs_straight",
                message="Stand tall with your legs straight.",
                passed_message="Ready!",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            )
        ]


# ─────────────────────────────────────────────────────────────
#  2. PUSH-UP
# ─────────────────────────────────────────────────────────────


class PushUp(BaseExercise):
    name = "push_up"
    display_name = "Push Up"
    START_CUE = "Get into a plank position with your arms fully extended."
    MIN_REP_DURATION = 1.0
    CALIBRATION_DURATION = 2.0
    TRACKED_LANDMARKS = ["shoulder", "elbow", "wrist", "hip", "ankle"]
    USES_REP_QUALITY_TRACKING = True

    def __init__(self):
        super().__init__()
        self._reached_down = False
        self._had_drift_this_rep = False


    def reset(self):
        super().reset()
        self._reached_down = False
        self._had_drift_this_rep = False


    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        # Determine the primary side dynamically based on higher landmark visibility
        left_vis = (
            visibility(lm, "left_shoulder") +
            visibility(lm, "left_elbow") +
            visibility(lm, "left_hip") +
            visibility(lm, "left_ankle")
        ) / 4.0

        right_vis = (
            visibility(lm, "right_shoulder") +
            visibility(lm, "right_elbow") +
            visibility(lm, "right_hip") +
            visibility(lm, "right_ankle")
        ) / 4.0

        side = "left" if left_vis >= right_vis else "right"

        elbow_angle = compute_angle(lm, f"{side}_shoulder", f"{side}_elbow", f"{side}_wrist", h, w)
        
        # Scale-Invariant Hip Deviation Calculation for Plank Alignment
        s_pt = get_coords(lm, f"{side}_shoulder", h, w)
        h_pt = get_coords(lm, f"{side}_hip", h, w)
        a_pt = get_coords(lm, f"{side}_ankle", h, w)

        torso_length = math.hypot(h_pt[0] - s_pt[0], h_pt[1] - s_pt[1]) + 1e-6
        
        if abs(a_pt[0] - s_pt[0]) > 1e-3:
            t = (h_pt[0] - s_pt[0]) / (a_pt[0] - s_pt[0])
            expected_hip_y = s_pt[1] + t * (a_pt[1] - s_pt[1])
        else:
            expected_hip_y = (s_pt[1] + a_pt[1]) / 2.0

        # Screen Y increases downward (negative = hips piking up, positive = hips sagging)
        norm_hip_dev = (h_pt[1] - expected_hip_y) / torso_length

        return {
            "elbow": elbow_angle,
            "norm_hip_dev": norm_hip_dev,
            "active_side": side,
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        elbow = angles.get("elbow", 180.0)

        # "up": Arms extended at lockout (>= 155°)
        if elbow >= 155.0:
            return "up"
        # "down": Chest lowered, elbows at 90 degrees or deeper (<= 90°)
        elif elbow <= 90.0:
            self._reached_down = True
            return "down"

        return "mid"

    def should_count(self) -> bool:
        # Rep counts when returning fully back to lockout "up" after reaching depth "down"
        if self.current_state == "up" and self._reached_down:
            self._reached_down = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        norm_dev = angles.get("norm_hip_dev", 0.0)

        # Form Check 1: Piking hips up into the air (deviation < -0.15)
        if norm_dev < -0.15:
            errors.append(FormError(
                message="Hips too high",
                speech="Lower your hips. Keep your body in a straight plank line.",
                severity="warning"
            ))
        
        # Form Check 2: Hips sagging toward the floor (deviation > 0.15)
        elif norm_dev > 0.15:
            errors.append(FormError(
                message="Hips sagging",
                speech="Engage your core. Don't let your hips drop.",
                severity="warning"
            ))

        return errors

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        return angles["elbow"] >= 150.0 and abs(angles["norm_hip_dev"]) <= 0.15

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="full_body_visible_side",
                message="Set up in side view so your shoulders, hips, and ankles are clearly visible.",
                passed_message="Full body profile detected.",
                check_fn=lambda lm, h, w: (
                    max(visibility(lm, "left_shoulder"), visibility(lm, "right_shoulder")) > 0.5 and
                    max(visibility(lm, "left_hip"), visibility(lm, "right_hip")) > 0.5 and
                    max(visibility(lm, "left_ankle"), visibility(lm, "right_ankle")) > 0.5
                ),
            ),
            CalibrationCheck(
                id="plank_straight_line",
                message="Get into a plank — form a straight line from shoulders to ankles.",
                passed_message="Plank alignment locked.",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
                maintain=True,
            ),
            CalibrationCheck(
                id="arms_extended",
                message="Support yourself with your arms fully straight.",
                passed_message="Starting position locked. Get ready!",
                check_fn=lambda lm, h, w: (
                    compute_angle(lm, "left_shoulder", "left_elbow", "left_wrist", h, w) > 150.0 or
                    compute_angle(lm, "right_shoulder", "right_elbow", "right_wrist", h, w) > 150.0
                ),
            )
        ]

# ─────────────────────────────────────────────────────────────
#  3. BICEP CURL
# ─────────────────────────────────────────────────────────────

class BicepCurl(BaseExercise):
    name = "bicep_curl"
    display_name = "Bicep Curl"
    START_CUE = "Tuck your elbows in. Start with your arms fully straight."
    MIN_REP_DURATION = 0.7
    CALIBRATION_DURATION = 2.0
    TRACKED_LANDMARKS = ["shoulder", "elbow", "wrist", "hip"]
    USES_REP_QUALITY_TRACKING = True

    def __init__(self):
        super().__init__()
        self._reached_up = False
        self._had_drift_this_rep = False


    def reset(self):
        super().reset()
        self._reached_up = False
        self._had_drift_this_rep = False


    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        left_elbow = compute_angle(lm, "left_shoulder", "left_elbow", "left_wrist", h, w)
        right_elbow = compute_angle(lm, "right_shoulder", "right_elbow", "right_wrist", h, w)

        # min() naturally tracks the arm currently curling. 
        # This brilliantly and seamlessly supports both Alternating AND Bilateral curls.
        curling_elbow = min(left_elbow, right_elbow)

        # Scale-Invariant Elbow Drift Calculation (Flaring out or swinging forward)
        ls = get_coords(lm, "left_shoulder", h, w)
        rs = get_coords(lm, "right_shoulder", h, w)
        le = get_coords(lm, "left_elbow", h, w)
        re = get_coords(lm, "right_elbow", h, w)
        lh = get_coords(lm, "left_hip", h, w)
        rh = get_coords(lm, "right_hip", h, w)

        # Use the maximum of shoulder width or torso length as our anatomical scale factor.
        # This prevents division-by-zero if the user stands fully side-facing to the camera.
        shoulder_width = math.hypot(ls[0] - rs[0], ls[1] - rs[1])
        torso_length = max(math.hypot(ls[0] - lh[0], ls[1] - lh[1]), math.hypot(rs[0] - rh[0], rs[1] - rh[1]))
        scale = max(shoulder_width, torso_length) + 1e-6

        # Measure horizontal displacement of the elbow from the shoulder
        l_drift = abs(le[0] - ls[0]) / scale
        r_drift = abs(re[0] - rs[0]) / scale

        return {
            "left_elbow": left_elbow,
            "right_elbow": right_elbow,
            "curling_elbow": curling_elbow,
            "l_drift": l_drift,
            "r_drift": r_drift
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        curling_elbow = angles.get("curling_elbow", 180.0)

        # "down": Arms extended at lockout (>= 145°)
        if curling_elbow >= 145.0:
            return "down"
        # "up": Bicep fully contracted (<= 60°)
        elif curling_elbow <= 60.0:
            self._reached_up = True
            return "up"

        return "mid"

    def should_count(self) -> bool:
        # Rep counts ONLY upon returning to full extension ("down") after contraction ("up")
        if self.current_state == "down" and self._reached_up:
            self._reached_up = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        left_elbow = angles.get("left_elbow", 180.0)
        right_elbow = angles.get("right_elbow", 180.0)
        curling_elbow = angles.get("curling_elbow", 180.0)
        
        # Evaluate drift ONLY on the arm(s) actively curling. 
        # Prevents false positive penalties on the resting arm during alternating curls.
        if left_elbow < 120.0 and right_elbow > 140.0:
            active_drift = angles.get("l_drift", 0.0)
        elif right_elbow < 120.0 and left_elbow > 140.0:
            active_drift = angles.get("r_drift", 0.0)
        else:
            active_drift = max(angles.get("l_drift", 0.0), angles.get("r_drift", 0.0))


        if self.prev_state == "down" and self.current_state != "down":
            self._had_drift_this_rep = False


        # Form Check: Elbow flaring wide or swinging forward (Momentum cheating)
        if active_drift > 0.30 and curling_elbow < 140.0:
            self._had_drift_this_rep = True
            errors.append(FormError(
                message="Elbows drifting",
                speech="Keep your elbows pinned to your sides. Don't let them swing.",
                severity="warning"
            ))

        return errors

    def get_rep_quality_errors(self) -> Optional[FormError]:
        had_drift = self._had_drift_this_rep
        self._had_drift_this_rep = False
        if had_drift:
            return FormError(
                message="Elbows drifting",
                speech="Keep your elbows pinned to your sides. Don't let them swing.",
                severity="warning"
            )
        return None

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        return angles["curling_elbow"] > 145.0

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="upper_body_visible",
                message="Step back so your upper body and arms are fully visible.",
                passed_message="Upper body detected.",
                check_fn=lambda lm, h, w: (
                    max(visibility(lm, "left_shoulder"), visibility(lm, "right_shoulder")) > 0.5 and
                    max(visibility(lm, "left_wrist"), visibility(lm, "right_wrist")) > 0.5 and
                    max(visibility(lm, "left_hip"), visibility(lm, "right_hip")) > 0.5
                ),
            ),
            CalibrationCheck(
                id="elbows_tucked",
                message="Tuck your elbows in close to your body.",
                passed_message="Elbows are tucked.",
                check_fn=self._elbows_tucked_ok,
                maintain=True,
            ),
            CalibrationCheck(
                id="arms_straight",
                message="Start with your arms fully straight, hanging down.",
                passed_message="Starting position locked. Get ready!",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            ),
        ]
        
    def _elbows_tucked_ok(self, lm, h: int, w: int) -> bool:
        try:
            angles = self.compute_angles(lm, h, w)
            return angles.get("l_drift", 1.0) < 0.25 and angles.get("r_drift", 1.0) < 0.25
        except Exception:
            return False

# ─────────────────────────────────────────────────────────────
#  4. HAMMER CURL
# ─────────────────────────────────────────────────────────────
class HammerCurl(BicepCurl):
    name = "hammer_curl"
    display_name = "Hammer Curl"
    START_CUE = "Let your arms hang straight, palms in."
    # Same mechanics as bicep curl, slightly different target angle
    # def check_form_errors(self, angles, lm, h, w):
    #     errors = []
    #     left = angles.get("left_elbow", 180)
    #     if self.current_state == "up" and left > 70:
    #         errors.append(FormError("Squeeze at top!", "Squeeze at the top. Keep your wrists neutral."))
    #     ls = get_coords(lm, "left_shoulder", h, w)
    #     le = get_coords(lm, "left_elbow", h, w)
    #     if abs(le[0] - ls[0]) > 80:
    #         errors.append(FormError("Elbows drifting", "Keep your elbows pinned to your sides."))
    #     return errors


# ─────────────────────────────────────────────────────────────
#  5. SHOULDER PRESS
# ─────────────────────────────────────────────────────────────

class ShoulderPress(BaseExercise):
    name = "shoulder_press"
    display_name = "Shoulder Press"
    START_CUE = "Hold your weights at shoulder height with your elbows bent."
    MIN_REP_DURATION = 1.0
    CALIBRATION_DURATION = 2.0
    TRACKED_LANDMARKS = ["shoulder", "elbow", "wrist"]

    def __init__(self):
        super().__init__()
        self._reached_up = False

    def reset(self):
        super().reset()
        self._reached_up = False

    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        left_elbow = compute_angle(lm, "left_shoulder", "left_elbow", "left_wrist", h, w)
        right_elbow = compute_angle(lm, "right_shoulder", "right_elbow", "right_wrist", h, w)
        avg_elbow = (left_elbow + right_elbow) / 2.0
        
        # Track left/right arm disparity to catch asymmetrical pressing
        elbow_diff = abs(left_elbow - right_elbow)

        # Verify whether wrists have successfully risen above shoulder level
        ls = get_coords(lm, "left_shoulder", h, w)
        rs = get_coords(lm, "right_shoulder", h, w)
        lw = get_coords(lm, "left_wrist", h, w)
        rw = get_coords(lm, "right_wrist", h, w)

        # Image Y increases downward, so smaller Y coordinates mean higher elevation
        wrist_above_shoulder = (lw[1] < ls[1]) and (rw[1] < rs[1])

        return {
            "left_elbow": left_elbow,
            "right_elbow": right_elbow,
            "avg_elbow": avg_elbow,
            "elbow_diff": elbow_diff,
            "wrist_above_shoulder": wrist_above_shoulder,
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        avg_elbow = angles.get("avg_elbow", 90.0)
        wrist_above = angles.get("wrist_above_shoulder", False)

        # "up": Arms fully extended overhead (>= 150°) with wrists above shoulders
        if avg_elbow >= 150.0 and wrist_above:
            self._reached_up = True
            return "up"
        # "down": Weights racked at shoulder height, elbows bent (<= 100°)
        elif avg_elbow <= 100.0:
            return "down"

        return "mid"

    def should_count(self) -> bool:
        # Rep counts when returning completely back to the starting rack position ("down") 
        # after successfully locking out overhead ("up").
        if self.current_state == "down" and self._reached_up:
            self._reached_up = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        avg_elbow = angles.get("avg_elbow", 90.0)
        elbow_diff = angles.get("elbow_diff", 0.0)

        # Form Check 1: Asymmetrical pressing (one arm pushing significantly faster/higher than the other)
        if elbow_diff > 25.0 and 100.0 < avg_elbow < 150.0:
            errors.append(FormError(
                message="Press evenly",
                speech="Push up evenly with both arms. Keep your movement balanced.",
                severity="warning"
            ))

        # Form Check 2: Incomplete lockout at top extension
        if 125.0 <= avg_elbow < 150.0 and self.current_state == "mid" and self.prev_state == "up":
            errors.append(FormError(
                message="Full lockout",
                speech="Fully extend your arms overhead at the top.",
                severity="warning"
            ))

        # Form Check 3: Failing to lower weights completely back down to shoulder height
        if 100.0 < avg_elbow <= 120.0 and self.current_state == "down" and self.prev_state == "mid":
            errors.append(FormError(
                message="Lower to shoulders",
                speech="Bring the weights all the way down to shoulder height before your next press.",
                severity="warning"
            ))

        return errors

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        return 75.0 <= angles["avg_elbow"] <= 110.0

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="upper_body_visible_frontal",
                message="Face the camera and step back so your upper body and arms are fully visible.",
                passed_message="Upper body detected.",
                check_fn=lambda lm, h, w: (
                    visibility(lm, "left_shoulder") > 0.5 and visibility(lm, "right_shoulder") > 0.5 and
                    visibility(lm, "left_wrist") > 0.5 and visibility(lm, "right_wrist") > 0.5
                ),
            ),
            CalibrationCheck(
                id="weights_at_shoulders",
                message="Hold your weights at shoulder height with elbows bent around 90 degrees.",
                passed_message="Starting position locked. Get ready!",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
                maintain=True,
            ),
        ]
# ─────────────────────────────────────────────────────────────
#  6. LATERAL RAISE
# ─────────────────────────────────────────────────────────────
class LateralRaise(BaseExercise):
    name = "lateral_raise"
    display_name = "Lateral Raise"
    START_CUE = "Arms relaxed, down by your sides."
    MIN_REP_DURATION = 0.8
    TRACKED_LANDMARKS = ["hip", "shoulder", "wrist"]

    def __init__(self):
        super().__init__()
        self._reached_up = False

    def reset(self):
        super().reset()
        self._reached_up = False


    def compute_angles(self, lm, h, w):
        # Use shoulder abduction via hip-shoulder-wrist
        return {
            "left_raise":  compute_angle(lm, "left_hip",  "left_shoulder",  "left_wrist",  h, w),
            "right_raise": compute_angle(lm, "right_hip", "right_shoulder", "right_wrist", h, w),
        }

    def get_fsm_state(self, angles, lm, h, w):
        avg = (angles.get("left_raise", 0) + angles.get("right_raise", 0)) / 2
        if avg < 40:
            return "down"
        elif avg >= 75:
            self._reached_up = True
            return "up"
        return "mid"

    def should_count(self):
        # Only counts after a genuine visit to "down" following "up" —
        # jitter bouncing between up/mid near the 75° boundary no longer
        # counts multiple reps for one raise.
        if self.current_state == "down" and self._reached_up:
            self._reached_up = False
            return True
        return False


    def check_form_errors(self, angles, lm, h, w):
        errors = []
        avg = (angles.get("left_raise", 0) + angles.get("right_raise", 0)) / 2
        if 60.0 < avg <= 74.0 and self.prev_state == "mid":
            errors.append(FormError("Raise higher", "Raise your arms to shoulder height."))

        # Hands too close together — arms should spread wide to the sides,
        # not stay narrow/in front of the body during the raise.
        if self.current_state in ("mid", "up"):
            lw = get_coords(lm, "left_wrist", h, w)
            rw = get_coords(lm, "right_wrist", h, w)
            ls = get_coords(lm, "left_shoulder", h, w)
            rs = get_coords(lm, "right_shoulder", h, w)
            wrist_dist = abs(lw[0] - rw[0])
            shoulder_width = abs(ls[0] - rs[0]) + 1e-6   # avoid div-by-zero
            if wrist_dist < shoulder_width * 1.4:
                errors.append(FormError(
                    "Hands too close",
                    "Your hands are too close for a lateral raise. Expand your arms out to your sides.",
                ))
        return errors

    def check_start_posture(self, lm, h, w):
        angle = compute_angle(lm, "left_hip", "left_shoulder", "left_wrist", h, w)
        return angle < 40

    def get_calibration_checks(self):
        return [
            CalibrationCheck(
                id="full_body_visible",
                message="Step back so your upper body is visible.",
                passed_message="Good, I can see you.",
                check_fn=lambda lm,h,w: visibility(lm,"left_shoulder")>0.4 and visibility(lm,"right_shoulder")>0.4,
                guide_fn=lambda lm,h,w: {
                    "left_x": get_coords(lm, "left_shoulder", h, w)[0],
                    "right_x": get_coords(lm, "right_shoulder", h, w)[0],
                }
            ),
            CalibrationCheck(
                id="arms_down",
                message="Arms relaxed down by your side.",
                passed_message="Good, I can see you.",
                check_fn=lambda lm, h, w: compute_angle(lm, "left_hip", "left_shoulder", "left_wrist", h, w) < 40
            ),
            CalibrationCheck(
                id="stance_width",
                message="Step closer so your stance is narrower.",
                passed_message="Good, your stance is good.",
                check_fn=lambda lm, h, w: compute_angle(lm, "left_shoulder", "left_hip", "left_knee", h, w) > 155 and compute_angle(lm, "right_shoulder", "right_hip", "right_knee", h, w) > 155,
                guide_fn=lambda lm, h, w: {
                    "left_x": get_coords(lm, "left_shoulder", h, w)[0],
                    "right_x": get_coords(lm, "right_shoulder", h, w)[0],
                }            
            )
        ]

# ─────────────────────────────────────────────────────────────
#  7. LUNGE
# ─────────────────────────────────────────────────────────────
class Lunge(BaseExercise):
    name = "lunge"
    display_name = "Lunge"
    START_CUE = "Stand tall with legs straight."
    MIN_REP_DURATION = 0.8
    TRACKED_LANDMARKS = ["hip", "knee", "ankle", "shoulder"]

    def __init__(self):
        super().__init__()
        self._reached_down = False

    def reset(self):
        super().reset()
        self._reached_down = False

    def compute_angles(self, lm, h, w):
        return {
            "left_knee":  compute_angle(lm, "left_hip",  "left_knee",  "left_ankle",  h, w),
            "right_knee": compute_angle(lm, "right_hip", "right_knee", "right_ankle", h, w),
        }

    def get_fsm_state(self, angles, lm, h, w):
        # Use the front leg (lower angle = deeper lunge)
        knee = min(angles.get("left_knee", 180), angles.get("right_knee", 180))
        if knee > 155:
            return "up"
        elif knee <= 100:
            self._reached_down = True
            return "down"
        return "mid"

    
    def should_count(self):
        # Only counts after a genuine return to "up" following "down" —
        # prevents double-counting from jitter near the depth threshold.
        if self.current_state == "up" and self._reached_down:
            self._reached_down = False
            return True
        return False


    def check_form_errors(self, angles, lm, h, w):
        errors = []
        lkx, _ = get_coords(lm, "left_knee", h, w)
        lax, _ = get_coords(lm, "left_ankle", h, w)
        ls = get_coords(lm, "left_shoulder", h, w)
        rs = get_coords(lm, "right_shoulder", h, w)

        # Body-normalized: scale the pixel offset by shoulder width so this
        # is resolution/distance-agnostic, matching Squat/PushUp/BicepCurl.
        shoulder_width = abs(ls[0] - rs[0]) + 1e-6
        knee_toe_ratio = abs(lkx - lax) / shoulder_width

        if knee_toe_ratio > 0.35:
            errors.append(FormError(
                "Knee over toe",
                "Keep your front knee aligned over your ankle.",
                severity="warning"
            ))
        return errors

    def check_start_posture(self, lm, h, w):
        knee = compute_angle(lm, "left_hip", "left_knee", "left_ankle", h, w)
        return knee > 155

    def get_calibration_checks(self):
        return [
            CalibrationCheck(
                id="full_body_visible",
                message="Step back so your upper body is visible.",
                passed_message="Good, I can see you.",
                check_fn=lambda lm,h,w: visibility(lm,"left_shoulder")>0.4 and visibility(lm,"right_shoulder")>0.4,
                guide_fn=lambda lm,h,w: {
                    "left_x": get_coords(lm, "left_shoulder", h, w)[0],
                    "right_x": get_coords(lm, "right_shoulder", h, w)[0],
                }
            ),
            CalibrationCheck(
                id="stance_too_wide",
                message="Step closer so your stance is narrower.",
                passed_message="Good, your stance is good.",
                check_fn=lambda lm,h,w: compute_angle(lm,"left_shoulder","left_hip","left_knee",h,w) >155 and compute_angle(lm,"right_shoulder","right_hip","right_knee",h,w) > 155,
                guide_fn=lambda lm,h,w: {
                    "left_x": get_coords(lm, "left_shoulder", h, w)[0],
                    "right_x": get_coords(lm, "right_shoulder", h, w)[0],
                }
            )
        ]


# ─────────────────────────────────────────────────────────────
#  8. SIDE LUNGE
# ─────────────────────────────────────────────────────────────

class SideLunge(BaseExercise):
    name = "side_lunge"
    display_name = "Side Lunge"
    START_CUE = "Stand facing the camera with feet wide and both legs straight."
    MIN_REP_DURATION = 0.8
    CALIBRATION_DURATION = 2.0
    TRACKED_LANDMARKS = ["hip", "knee", "ankle", "shoulder"]


    def __init__(self):
        super().__init__()
        self._reached_down = False

    def reset(self):
        super().reset()
        self._reached_down = False

    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        left_knee = compute_angle(lm, "left_hip", "left_knee", "left_ankle", h, w)
        right_knee = compute_angle(lm, "right_hip", "right_knee", "right_ankle", h, w)

        # Working leg is the bending knee (smaller angle); straight leg is the trailing leg
        working_knee = min(left_knee, right_knee)
        straight_knee = max(left_knee, right_knee)

        # Scale-Invariant Stance Width Ratio
        l_ankle = get_coords(lm, "left_ankle", h, w)
        r_ankle = get_coords(lm, "right_ankle", h, w)
        l_shoulder = get_coords(lm, "left_shoulder", h, w)
        r_shoulder = get_coords(lm, "right_shoulder", h, w)

        ankle_dist = math.hypot(l_ankle[0] - r_ankle[0], l_ankle[1] - r_ankle[1])
        shoulder_width = math.hypot(l_shoulder[0] - r_shoulder[0], l_shoulder[1] - r_shoulder[1]) + 1e-6

        stance_ratio = ankle_dist / shoulder_width

        return {
            "left_knee": left_knee,
            "right_knee": right_knee,
            "working_knee": working_knee,
            "straight_knee": straight_knee,
            "stance_ratio": stance_ratio,
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        working_knee = angles.get("working_knee", 180.0)

        # "up": Standing fully upright with both legs extended straight (working_knee >= 155°)
        if working_knee >= 155.0:
            return "up"
        # "down": Deep side lunge depth (working_knee <= 100°)
        elif working_knee <= 100.0:
            self._reached_down = True
            return "down"

        return "mid"

    def should_count(self) -> bool:
        # Rep counts upon returning fully upright ("up") after hitting peak depth ("down")
        if self.current_state == "up" and self._reached_down:
            self._reached_down = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        working_knee = angles.get("working_knee", 180.0)
        straight_knee = angles.get("straight_knee", 180.0)
        stance_ratio = angles.get("stance ratio", 2.0)


        # Form Check 1: Bending the trailing (non-lunging) leg instead of keeping it locked straight
        if working_knee < 125.0 and straight_knee < 155.0:
            errors.append(FormError(
                message="Keep one leg straight",
                speech="Keep your non-lunging leg completely straight as you sit back.",
                severity="warning"
            ))

        # Form Check 2: Shallow side lunge depth during descent
        if 100.0 < working_knee <= 125.0 and self.prev_state == "mid":
            errors.append(FormError(
                message="Lunge deeper",
                speech="Sink lower into your lunge until your thigh is parallel to the floor.",
                severity="warning"
            ))

        # Form Check 3: Stance too narrow for a real side lunge (feet too close together)
        if working_knee < 140.0 and stance_ratio < 1.3:
            errors.append(FormError(
                message="Widen your stance",
                speech="Take a wider step out to the side before lunging.",
                severity="warning"
            ))

        return errors

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        return angles["left_knee"] >= 155.0 and angles["right_knee"] >= 155.0

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="full_body_visible_frontal",
                message="Face the camera and step back so your full body from shoulders to ankles is visible.",
                passed_message="Full body profile detected.",
                check_fn=lambda lm, h, w: (
                    visibility(lm, "left_shoulder") > 0.5 and visibility(lm, "right_shoulder") > 0.5 and
                    visibility(lm, "left_hip") > 0.5 and visibility(lm, "right_hip") > 0.5 and
                    visibility(lm, "left_knee") > 0.5 and visibility(lm, "right_knee") > 0.5 and
                    visibility(lm, "left_ankle") > 0.5 and visibility(lm, "right_ankle") > 0.5
                ),
            ),
            CalibrationCheck(
                id="standing_upright_start",
                message="Stand tall facing forward with both legs straight.",
                passed_message="Starting position locked. Get ready!",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            ),
        ]

# ─────────────────────────────────────────────────────────────
#  9. DEADLIFT
# ─────────────────────────────────────────────────────────────

class Deadlift(BaseExercise):
    name = "deadlift"
    display_name = "Deadlift"
    START_CUE = "Stand upright with shoulders back and hips fully extended."
    MIN_REP_DURATION = 1.0
    CALIBRATION_DURATION = 2.0
    TRACKED_LANDMARKS = ["shoulder", "hip", "knee", "ankle", "ear"]

    def __init__(self):
        super().__init__()
        self._reached_down = False

    def reset(self):
        super().reset()
        self._reached_down = False

    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        # Determine the primary side dynamically based on landmark visibility
        left_vis = (
            visibility(lm, "left_shoulder") +
            visibility(lm, "left_hip") +
            visibility(lm, "left_knee") +
            visibility(lm, "left_ankle")
        ) / 4.0

        right_vis = (
            visibility(lm, "right_shoulder") +
            visibility(lm, "right_hip") +
            visibility(lm, "right_knee") +
            visibility(lm, "right_ankle")
        ) / 4.0

        side = "left" if left_vis >= right_vis else "right"

        hip_angle = compute_angle(lm, f"{side}_shoulder", f"{side}_hip", f"{side}_knee", h, w)
        knee_angle = compute_angle(lm, f"{side}_hip", f"{side}_knee", f"{side}_ankle", h, w)
        spine_angle = compute_angle(lm, f"{side}_ear", f"{side}_shoulder", f"{side}_hip", h, w)

        return {
            "hip": hip_angle,
            "knee": knee_angle,
            "spine": spine_angle,
            "active_side": side,
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        hip = angles.get("hip", 180.0)

        # "up": Standing upright with hips fully extended at lockout (>= 160°)
        if hip >= 160.0:
            return "up"
        # "down": Hinging down at the bottom of the movement (<= 100°)
        elif hip <= 100.0:
            self._reached_down = True
            return "down"

        return "mid"

    def should_count(self) -> bool:
        # Rep counts when returning upright ("up") after hitting the bottom hinge ("down")
        if self.current_state == "up" and self._reached_down:
            self._reached_down = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        hip = angles.get("hip", 180.0)
        knee = angles.get("knee", 180.0)
        spine = angles.get("spine", 180.0)

        # Form Check 1: Upper back spine rounding (flexion at upper torso)
        if spine < 145.0:
            errors.append(FormError(
                message="Keep back straight",
                speech="Keep your back flat and chest up. Avoid rounding your spine.",
                severity="warning"
            ))

        # Form Check 2: Squatting the deadlift (knee bend excessive relative to hip hinge)
        if hip <= 120.0 and knee < 85.0:
            errors.append(FormError(
                message="Hinge at hips",
                speech="Hinge at your hips rather than squatting down.",
                severity="warning"
            ))

        return errors

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        return angles["hip"] >= 160.0 and angles["knee"] >= 160.0

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="full_body_visible_side",
                message="Position camera in side view so shoulders, hips, knees, and ankles are visible.",
                passed_message="Full body profile detected.",
                check_fn=lambda lm, h, w: (
                    max(visibility(lm, "left_shoulder"), visibility(lm, "right_shoulder")) > 0.5 and
                    max(visibility(lm, "left_hip"), visibility(lm, "right_hip")) > 0.5 and
                    max(visibility(lm, "left_knee"), visibility(lm, "right_knee")) > 0.5 and
                    max(visibility(lm, "left_ankle"), visibility(lm, "right_ankle")) > 0.5
                ),
            ),
            CalibrationCheck(
                id="standing_upright_lockout",
                message="Stand tall with back straight and hips fully extended.",
                passed_message="Starting position locked. Get ready!",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            ),
        ]

# ─────────────────────────────────────────────────────────────
#  10. GLUTE BRIDGE
# ─────────────────────────────────────────────────────────────

class GluteBridge(BaseExercise):
    name = "glute_bridge"
    display_name = "Glute Bridge"
    START_CUE = "Lie flat on your back with knees bent and feet flat on the floor."
    MIN_REP_DURATION = 0.8
    CALIBRATION_DURATION = 2.0
    TRACKED_LANDMARKS = ["shoulder", "hip", "knee", "ankle"]

    def __init__(self):
        super().__init__()
        self._reached_up = False

    def reset(self):
        super().reset()
        self._reached_up = False

    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        # Determine the primary side dynamically based on landmark visibility
        left_vis = (
            visibility(lm, "left_shoulder") +
            visibility(lm, "left_hip") +
            visibility(lm, "left_knee") +
            visibility(lm, "left_ankle")
        ) / 4.0

        right_vis = (
            visibility(lm, "right_shoulder") +
            visibility(lm, "right_hip") +
            visibility(lm, "right_knee") +
            visibility(lm, "right_ankle")
        ) / 4.0

        side = "left" if left_vis >= right_vis else "right"

        hip_angle = compute_angle(lm, f"{side}_shoulder", f"{side}_hip", f"{side}_knee", h, w)
        knee_angle = compute_angle(lm, f"{side}_hip", f"{side}_knee", f"{side}_ankle", h, w)

        return {
            "hip": hip_angle,
            "knee": knee_angle,
            "active_side": side,
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        hip = angles.get("hip", 0.0)

        # "up": Hips driven high to align shoulder-hip-knee (>= 155°)
        if hip >= 155.0:
            self._reached_up = True
            return "up"
        # "down": Hips resting back near the floor (<= 105°)
        elif hip <= 105.0:
            return "down"

        return "mid"

    def should_count(self) -> bool:
        # Rep counts upon returning hips to floor ("down") after achieving full extension ("up")
        if self.current_state == "down" and self._reached_up:
            self._reached_up = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        hip = angles.get("hip", 0.0)
        knee = angles.get("knee", 180.0)

        # Form Check 1: Feet placed too far out from glutes (transfers focus to hamstrings)
        if knee > 125.0:
            errors.append(FormError(
                message="Bring feet closer",
                speech="Walk your feet closer to your glutes.",
                severity="warning"
            ))
        # Form Check 2: Feet placed too close to glutes (causes excessive knee flexion/quad strain)
        elif knee < 65.0:
            errors.append(FormError(
                message="Move feet forward",
                speech="Move your feet slightly further away from your glutes.",
                severity="warning"
            ))

        # Form Check 3: Incomplete hip lockout during thrust
        if 115.0 < hip < 145.0 and self.prev_state == "mid":
            errors.append(FormError(
                message="Squeeze glutes higher",
                speech="Squeeze your glutes and drive your hips all the way up.",
                severity="warning"
            ))

        return errors

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        return angles["hip"] <= 105.0 and (70.0 <= angles["knee"] <= 120.0)

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="full_body_visible_side",
                message="Position yourself lying down in side view so shoulders, hips, knees, and ankles are clear.",
                passed_message="Full body positioning detected.",
                check_fn=lambda lm, h, w: (
                    max(visibility(lm, "left_shoulder"), visibility(lm, "right_shoulder")) > 0.5 and
                    max(visibility(lm, "left_hip"), visibility(lm, "right_hip")) > 0.5 and
                    max(visibility(lm, "left_knee"), visibility(lm, "right_knee")) > 0.5 and
                    max(visibility(lm, "left_ankle"), visibility(lm, "right_ankle")) > 0.5
                ),
            ),
            CalibrationCheck(
                id="resting_glute_bridge_start",
                message="Lie flat on your back with knees bent and hips down.",
                passed_message="Starting position set. Get ready!",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            ),
        ]

# ─────────────────────────────────────────────────────────────
#  11. CALF RAISE
# ─────────────────────────────────────────────────────────────

class CalfRaise(BaseExercise):
    name = "calf_raise"
    display_name = "Calf Raise"
    START_CUE = "Stand flat-footed with your knees straight."
    MIN_REP_DURATION = 0.5   # calf raises are quick — was 0.7
    CALIBRATION_DURATION = 2.0
    TRACKED_LANDMARKS = ["hip", "knee", "ankle", "heel", "foot_index"]

    def __init__(self):
        super().__init__()
        self.baseline_heel_lift = 0.0
        self._reached_up_phase = False

    def reset(self):
        super().reset()
        self.baseline_heel_lift = 0.0
        self._reached_up_phase = False

    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        left_vis = (visibility(lm, "left_heel") + visibility(lm, "left_foot_index")) / 2.0
        right_vis = (visibility(lm, "right_heel") + visibility(lm, "right_foot_index")) / 2.0
        side = "left" if left_vis >= right_vis else "right"

        knee_angle = compute_angle(lm, f"{side}_hip", f"{side}_knee", f"{side}_ankle", h, w)

        # Heel-lift metric: vertical gap between heel and toe, normalized by
        # shin length. Orientation-tolerant — unlike the old knee-ankle-toe
        # angle, this changes with a heel lift regardless of whether the
        # camera sees the user from the front or the side, because "up" in
        # the real world is "up" (smaller y) in the image no matter which
        # way the user is rotated.
        heel = get_coords(lm, f"{side}_heel", h, w)
        toe = get_coords(lm, f"{side}_foot_index", h, w)
        knee = get_coords(lm, f"{side}_knee", h, w)
        ankle = get_coords(lm, f"{side}_ankle", h, w)

        shin_length = math.hypot(knee[0] - ankle[0], knee[1] - ankle[1]) + 1e-6
        # Screen Y increases downward, so a raised heel has a SMALLER y than
        # the planted toe — (toe_y - heel_y) grows positive as heel lifts.
        heel_lift = (toe[1] - heel[1]) / shin_length

        return {
            "knee_angle": knee_angle,
            "heel_lift": heel_lift,
            "active_side": side,
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        lift = angles.get("heel_lift", 0.0)

        # Track the flat-footed baseline while resting in "down" —
        # same adaptive-baseline idea as the old ankle-angle version, just
        # applied to the heel-lift ratio instead.
        if self.is_calibrated and self.current_state in (None, "down"):
            self.baseline_heel_lift = (0.85 * self.baseline_heel_lift) + (0.15 * lift)

        delta = lift - self.baseline_heel_lift

        if delta >= 0.18:
            self._reached_up_phase = True
            return "up"
        elif delta <= 0.05:
            return "down"

        return "mid"

    def should_count(self) -> bool:
        if self.current_state == "down" and self._reached_up_phase:
            self._reached_up_phase = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        knee_angle = angles.get("knee_angle", 180.0)

        if knee_angle < 155.0:
            errors.append(FormError(
                message="Keep knees straight",
                speech="Keep your legs straight and drive up through your toes.",
                severity="warning"
            ))

        return errors

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        # Flat-footed: heel and toe at roughly the same height
        return angles["heel_lift"] < 0.10

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="full_body_visible",
                message="Step back so your legs and feet are fully visible.",
                passed_message="Legs and feet detected.",
                check_fn=lambda lm, h, w: (
                    max(visibility(lm, "left_heel"), visibility(lm, "right_heel")) > 0.4 and
                    max(visibility(lm, "left_foot_index"), visibility(lm, "right_foot_index")) > 0.4
                ),
            ),
            CalibrationCheck(
                id="flat_footed",
                message="Stand upright and flat-footed with your heels down.",
                passed_message="Starting position locked. Get ready...",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            ),
        ]



# ─────────────────────────────────────────────────────────────
#  12. LEG RAISE
# ─────────────────────────────────────────────────────────────

class LegRaise(BaseExercise):
    name = "leg_raise"
    display_name = "Leg Raise"
    START_CUE = "Lie flat on your back with your legs straight."
    MIN_REP_DURATION = 0.8
    CALIBRATION_DURATION = 2.0
    TRACKED_LANDMARKS = ["shoulder", "hip", "knee", "ankle"]
    USES_REP_QUALITY_TRACKING = True


    def __init__(self):
        super().__init__()
        self._reached_up_phase = False
        self._had_bent_knee_this_rep = False

    def reset(self):
        super().reset()
        self._reached_up_phase = False
        self._had_bent_knee_this_rep = False

    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        # Determine the primary side dynamically based on higher landmark visibility
        left_vis = (
            visibility(lm, "left_shoulder") +
            visibility(lm, "left_hip") +
            visibility(lm, "left_knee") +
            visibility(lm, "left_ankle")
        ) / 4.0

        right_vis = (
            visibility(lm, "right_shoulder") +
            visibility(lm, "right_hip") +
            visibility(lm, "right_knee") +
            visibility(lm, "right_ankle")
        ) / 4.0

        side = "left" if left_vis >= right_vis else "right"

        hip_angle = compute_angle(lm, f"{side}_shoulder", f"{side}_hip", f"{side}_knee", h, w)
        knee_angle = compute_angle(lm, f"{side}_hip", f"{side}_knee", f"{side}_ankle", h, w)

        return {
            "hip": hip_angle,
            "knee": knee_angle,
            "active_side": side,
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        hip = angles.get("hip", 180.0)

        # "up" state: legs lifted perpendicular to torso (<= 95°)
        if hip <= 95.0:
            self._reached_up_phase = True
            return "up"
        # "down" state: legs lowered back near the ground (>= 155°)
        elif hip >= 155.0:
            return "down"

        return "mid"

    def should_count(self) -> bool:
        # Rep counts upon returning flat ("down") after hitting vertical extension ("up")
        if self.current_state == "down" and self._reached_up_phase:
            self._reached_up_phase = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        knee = angles.get("knee", 180.0)
        hip = angles.get("hip", 180.0)

        if self.prev_state == "down" and self.current_state != "down":
            self._had_bent_knee_this_rep = False


        # Biomechanical Check: Bending knees (cheating by using knee flexors/tucking knees)
        if hip < 150.0 and knee < 155.0:
            errors.append(FormError(
                message="Keep legs straight",
                speech="Keep your knees straight and locked throughout the raise.",
                severity="warning"
            ))

        return errors

    def get_rep_quality_errors(self) -> Optional[FormError]:
        had_bent = self._had_bent_knee_this_rep
        self._had_bent_knee_this_rep = False
        if had_bent:
            return FormError(
                message="Keep legs straight",
                speech="Keep your knees straight and locked throughout the raise.",
                severity="warning"
            )
        return None

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        # Ensure user is lying flat with both hips extended and knees straight
        return angles["hip"] >= 155.0 and angles["knee"] >= 160.0

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="full_body_visible",
                message="Lie down in side view so your shoulders, hips, and feet are visible.",
                passed_message="Body positioning detected.",
                check_fn=lambda lm, h, w: (
                    max(visibility(lm, "left_shoulder"), visibility(lm, "right_shoulder")) > 0.5 and
                    max(visibility(lm, "left_hip"), visibility(lm, "right_hip")) > 0.5 and
                    max(visibility(lm, "left_ankle"), visibility(lm, "right_ankle")) > 0.5
                ),
            ),
            CalibrationCheck(
                id="lying_flat",
                message="Lie flat on your back with legs extended straight.",
                passed_message="Starting position set. Get ready...",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            ),
        ]

# ─────────────────────────────────────────────────────────────
#  13. PLANK (Duration-based)
# ─────────────────────────────────────────────────────────────


class Plank(BaseExercise):
    name = "plank"
    display_name = "Plank"
    IS_DURATION_BASED: bool = True   
    START_CUE = "Maintain a straight line from shoulders to ankles."
    MIN_REP_DURATION = 5.0   # Minimum hold duration (seconds) to register a valid hold block
    CALIBRATION_DURATION = 2.5
    TRACKED_LANDMARKS = ["shoulder", "hip", "ankle"]


    def __init__(self):
        super().__init__()
        self._hold_start_time = 0.0
        self._was_holding = False

    def reset(self):
        super().reset()
        self._hold_start_time = 0.0
        self._was_holding = False

    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        # Determine the primary side dynamically based on landmark visibility
        left_vis = (
            visibility(lm, "left_shoulder") + 
            visibility(lm, "left_hip") + 
            visibility(lm, "left_ankle")
        ) / 3.0

        right_vis = (
            visibility(lm, "right_shoulder") + 
            visibility(lm, "right_hip") + 
            visibility(lm, "right_ankle")
        ) / 3.0

        side = "left" if left_vis >= right_vis else "right"

        s_pt = get_coords(lm, f"{side}_shoulder", h, w)
        h_pt = get_coords(lm, f"{side}_hip", h, w)
        a_pt = get_coords(lm, f"{side}_ankle", h, w)

        body_angle = compute_angle(lm, f"{side}_shoulder", f"{side}_hip", f"{side}_ankle", h, w)

        # Scale-Invariant Hip Deviation Calculation:
        # Measures how far the hip deviates vertically from the straight line between shoulder and ankle,
        # normalized by torso length (distance from shoulder to hip).
        torso_length = math.hypot(h_pt[0] - s_pt[0], h_pt[1] - s_pt[1]) + 1e-6

        # Expected Y coordinate of the hip on the shoulder-ankle linear interpolation line
        if abs(a_pt[0] - s_pt[0]) > 1e-3:
            t = (h_pt[0] - s_pt[0]) / (a_pt[0] - s_pt[0])
            expected_hip_y = s_pt[1] + t * (a_pt[1] - s_pt[1])
        else:
            expected_hip_y = (s_pt[1] + a_pt[1]) / 2.0

        # Screen coordinates Y increases downwards:
        # (h_pt[1] < expected_hip_y) means hips are higher in screen space (piking UP)
        # (h_pt[1] > expected_hip_y) means hips are lower in screen space (sagging DOWN)
        norm_hip_dev = (h_pt[1] - expected_hip_y) / torso_length

        return {
            "body_line": body_angle,
            "norm_hip_dev": norm_hip_dev,
            "active_side": side
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        body = angles.get("body_line", 0.0)
        norm_dev = angles.get("norm_hip_dev", 0.0)

        # Solid plank: Body angle in neutral range and normalized hip deviation within tolerance (±12% of torso length)
        if 160.0 <= body <= 180.0 and abs(norm_dev) <= 0.12:
            if not self._was_holding:
                self._hold_start_time = self._current_time
                self._was_holding = True
            return "hold"
        
        self._was_holding = False
        return "break"

    def should_count(self) -> bool:
        # Count a hold rep when exiting a valid hold state that lasted at least MIN_REP_DURATION
        if self.prev_state == "hold" and self.current_state == "break":
            held = self._current_time - self._hold_start_time
            return held >= self.MIN_REP_DURATION
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        norm_dev = angles.get("norm_hip_dev", 0.0)

        # Negative deviation = hips above expected straight line (Screen Y is smaller)
        if norm_dev < -0.12:
            errors.append(FormError(
                message="Hips too high",
                speech="Lower your hips into a straight plank position.",
                severity="warning"
            ))
        # Positive deviation = hips below expected straight line (Screen Y is larger)
        elif norm_dev > 0.12:
            errors.append(FormError(
                message="Hips sagging",
                speech="Engage your core and lift your hips.",
                severity="warning"
            ))

        return errors

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        return 160.0 <= angles["body_line"] <= 180.0 and abs(angles["norm_hip_dev"]) <= 0.12

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="full_body_visible",
                message="Position camera in side view so your shoulders, hips, and feet are visible.",
                passed_message="Body line detected.",
                check_fn=lambda lm, h, w: (
                    max(visibility(lm, "left_shoulder"), visibility(lm, "right_shoulder")) > 0.5 and
                    max(visibility(lm, "left_hip"), visibility(lm, "right_hip")) > 0.5 and
                    max(visibility(lm, "left_ankle"), visibility(lm, "right_ankle")) > 0.5
                ),
            ),
            CalibrationCheck(
                id="plank_hold_start",
                message="Get into a straight plank position and hold still.",
                passed_message="Plank alignment verified. Hold it!",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            ),
        ]

# ─────────────────────────────────────────────────────────────
#  14. WALL SIT (Duration-based)
# ─────────────────────────────────────────────────────────────

class WallSit(BaseExercise):
    name = "wall_sit"
    display_name = "Wall Sit"
    IS_DURATION_BASED: bool = True
    START_CUE = "Slide back against the wall and bend your knees to 90 degrees."
    MIN_REP_DURATION = 5.0   # Minimum hold time (seconds) to log a valid hold block
    CALIBRATION_DURATION = 2.5
    TRACKED_LANDMARKS = ["shoulder", "hip", "knee", "ankle"]

    def __init__(self):
        super().__init__()
        self._hold_start_time = 0.0
        self._was_holding = False

    def reset(self):
        super().reset()
        self._hold_start_time = 0.0
        self._was_holding = False

    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        # Determine the primary side dynamically based on landmark visibility
        left_vis = (
            visibility(lm, "left_shoulder") +
            visibility(lm, "left_hip") +
            visibility(lm, "left_knee") +
            visibility(lm, "left_ankle")
        ) / 4.0

        right_vis = (
            visibility(lm, "right_shoulder") +
            visibility(lm, "right_hip") +
            visibility(lm, "right_knee") +
            visibility(lm, "right_ankle")
        ) / 4.0

        side = "left" if left_vis >= right_vis else "right"

        # Knee angle (Hip -> Knee -> Ankle): Target ~90°
        knee_angle = compute_angle(lm, f"{side}_hip", f"{side}_knee", f"{side}_ankle", h, w)
        
        # Hip angle (Shoulder -> Hip -> Knee): Target ~90° (Upright back against wall)
        hip_angle = compute_angle(lm, f"{side}_shoulder", f"{side}_hip", f"{side}_knee", h, w)

        return {
            "knee": knee_angle,
            "hip": hip_angle,
            "active_side": side
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        knee = angles.get("knee", 180.0)
        hip = angles.get("hip", 180.0)

        # Valid Wall Sit: Knee angle between 80° and 105°, Hip angle between 75° and 115°
        if (80.0 <= knee <= 105.0) and (75.0 <= hip <= 115.0):
            if not self._was_holding:
                self._hold_start_time = self._current_time
                self._was_holding = True
            return "hold"
        
        self._was_holding = False
        return "break"

    def should_count(self) -> bool:
        # Count a completed hold set when exiting 'hold' after maintaining it for at least MIN_REP_DURATION
        if self.prev_state == "hold" and self.current_state == "break":
            held = self._current_time - self._hold_start_time
            return held >= self.MIN_REP_DURATION
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        knee = angles.get("knee", 180.0)
        hip = angles.get("hip", 180.0)

        # Form Check 1: Hips sliding too high up the wall
        if knee > 105.0:
            errors.append(FormError(
                message="Sink lower",
                speech="Sink lower until your thighs are parallel to the floor.",
                severity="warning"
            ))
        # Form Check 2: Sitting too low / dropping hips below knees
        elif knee < 75.0:
            errors.append(FormError(
                message="Too low",
                speech="Raise your hips slightly to bring knees to 90 degrees.",
                severity="warning"
            ))

        # Form Check 3: Leaning torso forward off the wall
        if hip < 75.0:
            errors.append(FormError(
                message="Keep back flat",
                speech="Keep your back flat against the wall and chest up.",
                severity="warning"
            ))

        return errors

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        return (80.0 <= angles["knee"] <= 105.0) and (75.0 <= angles["hip"] <= 115.0)

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="full_body_visible",
                message="Stand against the wall in side view so your shoulders, hips, knees, and feet are visible.",
                passed_message="Body positioning detected.",
                check_fn=lambda lm, h, w: (
                    max(visibility(lm, "left_shoulder"), visibility(lm, "right_shoulder")) > 0.5 and
                    max(visibility(lm, "left_hip"), visibility(lm, "right_hip")) > 0.5 and
                    max(visibility(lm, "left_knee"), visibility(lm, "right_knee")) > 0.5 and
                    max(visibility(lm, "left_ankle"), visibility(lm, "right_ankle")) > 0.5
                ),
            ),
            CalibrationCheck(
                id="wall_sit_hold_start",
                message="Slide down into a wall sit with thighs parallel to the ground and hold.",
                passed_message="Wall sit position locked. Hold it!",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            ),
        ]

# ─────────────────────────────────────────────────────────────
#  15. JUMPING JACKS
# ─────────────────────────────────────────────────────────────


class JumpingJack(BaseExercise):
    name = "jumping_jack"
    display_name = "Jumping Jacks"
    START_CUE = "Stand tall facing the camera, arms down at sides, feet together."
    MIN_REP_DURATION = 0.4
    CALIBRATION_DURATION = 2.0
    TRACKED_LANDMARKS = ["hip", "shoulder", "wrist", "ankle"]
    USES_REP_QUALITY_TRACKING = True

    def __init__(self):
        super().__init__()
        self._reached_open = False
        self._had_feet_narrow_this_rep = False

    def reset(self):
        super().reset()
        self._reached_open = False
        self._had_feet_narrow_this_rep = False

    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        # Shoulder abduction angles (Hip -> Shoulder -> Wrist) for both sides
        left_arm = compute_angle(lm, "left_hip", "left_shoulder", "left_wrist", h, w)
        right_arm = compute_angle(lm, "right_hip", "right_shoulder", "right_wrist", h, w)
        avg_arm = (left_arm + right_arm) / 2.0

        # Scale-Invariant Stance Width Ratio: Ankle Distance / Shoulder Width
        l_ankle = get_coords(lm, "left_ankle", h, w)
        r_ankle = get_coords(lm, "right_ankle", h, w)
        l_shoulder = get_coords(lm, "left_shoulder", h, w)
        r_shoulder = get_coords(lm, "right_shoulder", h, w)

        ankle_dist = math.hypot(l_ankle[0] - r_ankle[0], l_ankle[1] - r_ankle[1])
        shoulder_width = math.hypot(l_shoulder[0] - r_shoulder[0], l_shoulder[1] - r_shoulder[1]) + 1e-6

        stance_ratio = ankle_dist / shoulder_width

        return {
            "left_arm": left_arm,
            "right_arm": right_arm,
            "avg_arm": avg_arm,
            "stance_ratio": stance_ratio,
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        avg_arm = angles.get("avg_arm", 0.0)
        stance = angles.get("stance_ratio", 0.0)

        # "open": Arms high overhead (>= 130°) AND feet jumped out wide (stance ratio >= 1.2)
        if avg_arm >= 130.0 and stance >= 1.2:
            self._reached_open = True
            return "open"
        # "closed": Arms down at sides (<= 45°) AND feet together (stance ratio <= 0.95)
        elif avg_arm <= 45.0 and stance <= 0.95:
            return "closed"

        return "mid"

    def should_count(self) -> bool:
        # Rep completes upon returning to "closed" after reaching peak "open" position
        if self.current_state == "closed" and self._reached_open:
            self._reached_open = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        avg_arm = angles.get("avg_arm", 0.0)
        stance = angles.get("stance_ratio", 0.0)

        if self.prev_state == "closed" and self.current_state != "closed":
            self._had_arms_low_this_rep = False
            self._had_feet_narrow_this_rep = False

        # Form Error 1: Feet jumped wide, but arms not raised overhead
        if stance >= 1.2 and avg_arm < 115.0:
            errors.append(FormError(
                message="Raise arms higher",
                speech="Raise your arms fully above your head.",
                severity="warning"
            ))
        # Form Error 2: Arms raised overhead, but feet not jumped out wide
        elif avg_arm >= 130.0 and stance < 1.05:
            errors.append(FormError(
                message="Jump wider",
                speech="Jump your feet out wider to at least shoulder width.",
                severity="warning"
            ))

        return errors


    def get_rep_quality_errors(self) -> Optional[FormError]:
        had_arms_low = self._had_arms_low_this_rep
        had_feet_narrow = self._had_feet_narrow_this_rep
        self._had_arms_low_this_rep = False
        self._had_feet_narrow_this_rep = False
        if had_arms_low:
            return FormError(
                message="Raise arms higher",
                speech="Raise your arms fully above your head.",
                severity="warning"
            )
        if had_feet_narrow:
            return FormError(
                message="Jump wider",
                speech="Jump your feet out wider to at least shoulder width.",
                severity="warning"
            )
        return None


    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        # Neutral stance: arms at sides (<= 40°) and feet together (stance ratio <= 1.0)
        return angles["avg_arm"] <= 40.0 and angles["stance_ratio"] <= 1.0

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="full_body_visible_frontal",
                message="Face the camera so your hands, feet, and whole body are visible.",
                passed_message="Full body detected.",
                check_fn=lambda lm, h, w: (
                    visibility(lm, "left_shoulder") > 0.5 and visibility(lm, "right_shoulder") > 0.5 and
                    visibility(lm, "left_wrist") > 0.5 and visibility(lm, "right_wrist") > 0.5 and
                    visibility(lm, "left_ankle") > 0.5 and visibility(lm, "right_ankle") > 0.5
                ),
            ),
            CalibrationCheck(
                id="neutral_standing_start",
                message="Stand tall facing forward with feet together and arms down at your sides.",
                passed_message="Starting position locked. Get ready!",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            ),
        ]

# ─────────────────────────────────────────────────────────────
#  16. HIGH KNEES
# ─────────────────────────────────────────────────────────────

class HighKnees(BaseExercise):
    name = "high_knees"
    display_name = "High Knees"
    START_CUE = "Stand tall with legs straight and arms at your side."
    MIN_REP_DURATION = 0.3
    CALIBRATION_DURATION = 2.0
    TRACKED_LANDMARKS = ["shoulder", "hip", "knee", "ankle"]
    USES_REP_QUALITY_TRACKING = True

    def __init__(self):
        super().__init__()
        self._reached_knee_up = False
        self._had_shallow_this_rep = False
        

    def reset(self):
        super().reset()
        self._reached_knee_up = False
        self._had_shallow_this_rep = False

    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        left_hip = compute_angle(lm, "left_shoulder", "left_hip", "left_knee", h, w)
        right_hip = compute_angle(lm, "right_shoulder", "right_hip", "right_knee", h, w)
        
        left_knee = compute_angle(lm, "left_hip", "left_knee", "left_ankle", h, w)
        right_knee = compute_angle(lm, "right_hip", "right_knee", "right_ankle", h, w)

        # Active leg has the smaller hip angle (highest knee raise)
        active_hip = min(left_hip, right_hip)

        return {
            "left_hip": left_hip,
            "right_hip": right_hip,
            "left_knee": left_knee,
            "right_knee": right_knee,
            "active_hip": active_hip,
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        active_hip = angles.get("active_hip", 180.0)
        left_hip = angles.get("left_hip", 180.0)
        right_hip = angles.get("right_hip", 180.0)

        # "knee_up": Thigh raised near parallel to floor (<= 95°)
        if active_hip <= 95.0:
            self._reached_knee_up = True
            return "knee_up"
        # "down": Both legs extended straight down (>= 150°)
        elif left_hip >= 150.0 and right_hip >= 150.0:
            return "down"

        return "mid"

    def should_count(self) -> bool:
        # Rep counts when returning to "down" after driving knee up above parallel
        if self.current_state == "down" and self._reached_knee_up:
            self._reached_knee_up = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        active_hip = angles.get("active_hip", 180.0)

        if self.prev_state == "down" and self.current_state != "down":
            self._had_shallow_this_rep = False

        # Form Check: Half-rep / Knee not raised high enough during drive (95° < active_hip <= 120°)
        if 95.0 < active_hip <= 120.0:
            errors.append(FormError(
                message="Lift knees higher",
                speech="Drive your knees up higher until your thighs are parallel to the floor.",
                severity="warning"
            ))

        return errors

    def get_rep_quality_errors(self) -> Optional[FormError]:
        had_shallow = self._had_shallow_this_rep
        self._had_shallow_this_rep = False
        if had_shallow:
            return FormError(
                message="Lift knees higher",
                speech="Drive your knees up higher until your thighs are parallel to the floor.",
                severity="warning"
            )
        return None

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        return angles["left_hip"] >= 155.0 and angles["right_hip"] >= 155.0

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="full_body_visible",
                message="Step back so your full body from shoulders to ankles is visible.",
                passed_message="Full body detected.",
                check_fn=lambda lm, h, w: (
                    max(visibility(lm, "left_shoulder"), visibility(lm, "right_shoulder")) > 0.5 and
                    max(visibility(lm, "left_hip"), visibility(lm, "right_hip")) > 0.5 and
                    max(visibility(lm, "left_knee"), visibility(lm, "right_knee")) > 0.5 and
                    max(visibility(lm, "left_ankle"), visibility(lm, "right_ankle")) > 0.5
                ),
            ),
            CalibrationCheck(
                id="standing_upright_start",
                message="Stand tall with both legs straight.",
                passed_message="Starting position locked. Get ready!",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            ),
        ]
# ─────────────────────────────────────────────────────────────
#  17. MOUNTAIN CLIMBER
# ─────────────────────────────────────────────────────────────

class MountainClimber(BaseExercise):
    name = "mountain_climber"
    display_name = "Mountain Climbers"
    START_CUE = "Get into a straight-arm plank in side view."
    MIN_REP_DURATION = 0.3
    CALIBRATION_DURATION = 2.0
    TRACKED_LANDMARKS = ["shoulder", "hip", "knee", "ankle"]

    def __init__(self):
        super().__init__()
        self._reached_knee_in = False

    def reset(self):
        super().reset()
        self._reached_knee_in = False

    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        # Determine the primary side dynamically based on higher landmark visibility
        left_vis = (
            visibility(lm, "left_shoulder") +
            visibility(lm, "left_hip") +
            visibility(lm, "left_knee") +
            visibility(lm, "left_ankle")
        ) / 4.0

        right_vis = (
            visibility(lm, "right_shoulder") +
            visibility(lm, "right_hip") +
            visibility(lm, "right_knee") +
            visibility(lm, "right_ankle")
        ) / 4.0

        side = "left" if left_vis >= right_vis else "right"

        left_hip = compute_angle(lm, "left_shoulder", "left_hip", "left_knee", h, w)
        right_hip = compute_angle(lm, "right_shoulder", "right_hip", "right_knee", h, w)
        
        # Active leg driving forward has the smaller hip angle
        active_hip = min(left_hip, right_hip)

        # Scale-Invariant Hip Deviation Calculation for Plank Alignment
        s_pt = get_coords(lm, f"{side}_shoulder", h, w)
        h_pt = get_coords(lm, f"{side}_hip", h, w)
        a_pt = get_coords(lm, f"{side}_ankle", h, w)

        torso_length = math.hypot(h_pt[0] - s_pt[0], h_pt[1] - s_pt[1]) + 1e-6
        
        if abs(a_pt[0] - s_pt[0]) > 1e-3:
            t = (h_pt[0] - s_pt[0]) / (a_pt[0] - s_pt[0])
            expected_hip_y = s_pt[1] + t * (a_pt[1] - s_pt[1])
        else:
            expected_hip_y = (s_pt[1] + a_pt[1]) / 2.0

        # Screen Y increases downward (negative = hips piking up, positive = hips sagging)
        norm_hip_dev = (h_pt[1] - expected_hip_y) / torso_length

        return {
            "left_hip": left_hip,
            "right_hip": right_hip,
            "active_hip": active_hip,
            "norm_hip_dev": norm_hip_dev,
            "active_side": side,
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        active_hip = angles.get("active_hip", 180.0)
        left_hip = angles.get("left_hip", 180.0)
        right_hip = angles.get("right_hip", 180.0)

        # "knee_in": One knee driven up toward chest (<= 95°)
        if active_hip <= 95.0:
            self._reached_knee_in = True
            return "knee_in"
        # "extended": Both legs extended back near straight plank (>= 145°)
        elif left_hip >= 145.0 and right_hip >= 145.0:
            return "extended"

        return "mid"

    def should_count(self) -> bool:
        # Rep counts when returning to "extended" after driving a knee in
        if self.current_state == "extended" and self._reached_knee_in:
            self._reached_knee_in = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        norm_dev = angles.get("norm_hip_dev", 0.0)
        active_hip = angles.get("active_hip", 180.0)

        # Form Check 1: Piking hips up into air (norm_dev < -0.15)
        if norm_dev < -0.15:
            errors.append(FormError(
                message="Keep hips down",
                speech="Keep your hips in line with your shoulders and plank.",
                severity="warning"
            ))
        # Form Check 2: Shallow knee drive (95° < active_hip <= 120°)
        elif 95.0 < active_hip <= 120.0:
            errors.append(FormError(
                message="Drive knee closer",
                speech="Drive your knee closer toward your chest.",
                severity="warning"
            ))

        return errors

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        return angles["left_hip"] >= 145.0 and angles["right_hip"] >= 145.0 and abs(angles["norm_hip_dev"]) <= 0.15

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="full_body_visible_side",
                message="Set up in side view so shoulders, hips, knees, and ankles are visible.",
                passed_message="Body alignment detected.",
                check_fn=lambda lm, h, w: (
                    max(visibility(lm, "left_shoulder"), visibility(lm, "right_shoulder")) > 0.5 and
                    max(visibility(lm, "left_hip"), visibility(lm, "right_hip")) > 0.5 and
                    max(visibility(lm, "left_ankle"), visibility(lm, "right_ankle")) > 0.5
                ),
            ),
            CalibrationCheck(
                id="straight_plank_start",
                message="Hold a solid straight-arm plank to begin.",
                passed_message="Plank position locked. Get ready!",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            ),
        ]

# ─────────────────────────────────────────────────────────────
#  18. TRICEP DIP
# ─────────────────────────────────────────────────────────────

class TricepDip(BaseExercise):
    name = "tricep_dip"
    display_name = "Tricep Dip"
    START_CUE = "Sit on edge of chair/bench with arms fully extended."
    MIN_REP_DURATION = 0.8
    CALIBRATION_DURATION = 2.0
    TRACKED_LANDMARKS = ["shoulder", "elbow", "wrist"]

    def __init__(self):
        super().__init__()
        self._reached_down = False

    def reset(self):
        super().reset()
        self._reached_down = False

    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        # Determine the primary side dynamically based on landmark visibility
        left_vis = (
            visibility(lm, "left_shoulder") +
            visibility(lm, "left_elbow") +
            visibility(lm, "left_wrist")
        ) / 3.0

        right_vis = (
            visibility(lm, "right_shoulder") +
            visibility(lm, "right_elbow") +
            visibility(lm, "right_wrist")
        ) / 3.0

        side = "left" if left_vis >= right_vis else "right"

        elbow_angle = compute_angle(lm, f"{side}_shoulder", f"{side}_elbow", f"{side}_wrist", h, w)
        
        # Scale-Invariant Elbow Flare Check (elbow horizontal offset relative to upper arm length)
        ls = get_coords(lm, f"{side}_shoulder", h, w)
        le = get_coords(lm, f"{side}_elbow", h, w)
        upper_arm_length = math.hypot(le[0] - ls[0], le[1] - ls[1]) + 1e-6
        elbow_horizontal_offset = abs(le[0] - ls[0]) / upper_arm_length

        return {
            "elbow": elbow_angle,
            "elbow_flare_ratio": elbow_horizontal_offset,
            "active_side": side,
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        elbow = angles.get("elbow", 180.0)

        # "up": Arms extended at lockout (>= 150°)
        if elbow >= 150.0:
            return "up"
        # "down": Elbows bent to 90 degrees or deeper (<= 95°)
        elif elbow <= 95.0:
            self._reached_down = True
            return "down"

        return "mid"

    def should_count(self) -> bool:
        # Rep counts upon returning all the way back to lockout "up" after reaching depth "down"
        if self.current_state == "up" and self._reached_down:
            self._reached_down = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        elbow = angles.get("elbow", 180.0)
        flare_ratio = angles.get("elbow_flare_ratio", 0.0)

        # Form Check 1: Shallow dips during descending phase (95° < elbow <= 115°)
        if 95.0 < elbow <= 115.0 and self.prev_state != "up":
            errors.append(FormError(
                message="Dip lower",
                speech="Dip lower until your elbows are at a 90-degree angle.",
                severity="warning"
            ))

        # Form Check 2: Elbows flaring excessively backward/outward relative to upper arm length
        if flare_ratio > 0.8:
            errors.append(FormError(
                message="Keep elbows tucked",
                speech="Keep your elbows tucked back close to your body.",
                severity="warning"
            ))

        return errors

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        return angles["elbow"] >= 150.0

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="full_upper_body_visible",
                message="Position camera in side view so shoulders, elbows, and wrists are clear.",
                passed_message="Upper body detected.",
                check_fn=lambda lm, h, w: (
                    max(visibility(lm, "left_shoulder"), visibility(lm, "right_shoulder")) > 0.5 and
                    max(visibility(lm, "left_elbow"), visibility(lm, "right_elbow")) > 0.5 and
                    max(visibility(lm, "left_wrist"), visibility(lm, "right_wrist")) > 0.5
                ),
            ),
            CalibrationCheck(
                id="arm_lockout_start",
                message="Support yourself with arms fully straight.",
                passed_message="Starting position locked. Get ready!",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            ),
        ]



# ─────────────────────────────────────────────────────────────
#  19. HORIZONTAL PRESS (Bench / Chest Press family)
#  Lying on back, pressing weight vertically upward.
#  Side-view camera. Elbow angle + wrists above shoulders at lockout.
#  Unlocks: DB/BB Bench, Incline Bench, Chest Press Machine, Close-Grip Bench
# ─────────────────────────────────────────────────────────────


class HorizontalPress(BaseExercise):
    name = "horizontal_press"
    display_name = "Horizontal Press"
    START_CUE = "Lie on your back with elbows bent and weights at chest level."
    MIN_REP_DURATION = 0.9
    CALIBRATION_DURATION = 2.0
    TRACKED_LANDMARKS = ["shoulder", "elbow", "wrist", "hip"]

    def __init__(self):
        super().__init__()
        self._reached_up = False

    def reset(self):
        super().reset()
        self._reached_up = False

    def _active_side(self, lm, h: int, w: int) -> str:
        left_vis = (
            visibility(lm, "left_shoulder")
            + visibility(lm, "left_elbow")
            + visibility(lm, "left_wrist")
        ) / 3.0
        right_vis = (
            visibility(lm, "right_shoulder")
            + visibility(lm, "right_elbow")
            + visibility(lm, "right_wrist")
        ) / 3.0
        return "left" if left_vis >= right_vis else "right"

    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        side = self._active_side(lm, h, w)
        elbow = compute_angle(lm, f"{side}_shoulder", f"{side}_elbow", f"{side}_wrist", h, w)

        left_elbow = compute_angle(lm, "left_shoulder", "left_elbow", "left_wrist", h, w)
        right_elbow = compute_angle(lm, "right_shoulder", "right_elbow", "right_wrist", h, w)

        ls = get_coords(lm, "left_shoulder", h, w)
        rs = get_coords(lm, "right_shoulder", h, w)
        lw = get_coords(lm, "left_wrist", h, w)
        rw = get_coords(lm, "right_wrist", h, w)

        # Screen Y increases downward — smaller Y = higher on screen
        wrist_above_shoulder = (lw[1] < ls[1]) and (rw[1] < rs[1])

        lh = get_coords(lm, "left_hip", h, w)
        rh = get_coords(lm, "right_hip", h, w)
        shoulder_y = (ls[1] + rs[1]) / 2.0
        hip_y = (lh[1] + rh[1]) / 2.0
        torso_len = abs(hip_y - shoulder_y) + 1e-6
        torso_tilt = (hip_y - shoulder_y) / torso_len

        return {
            "elbow": elbow,
            "left_elbow": left_elbow,
            "right_elbow": right_elbow,
            "elbow_diff": abs(left_elbow - right_elbow),
            "wrist_above_shoulder": 1.0 if wrist_above_shoulder else 0.0,
            "torso_tilt": torso_tilt,
            "active_side": side,
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        elbow = angles.get("elbow", 90.0)
        wrist_above = angles.get("wrist_above_shoulder", 0.0) >= 0.5

        if elbow >= 150.0 and wrist_above:
            self._reached_up = True
            return "up"
        if elbow <= 95.0:
            return "down"
        return "mid"

    def should_count(self) -> bool:
        if self.current_state == "down" and self._reached_up:
            self._reached_up = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        elbow = angles.get("elbow", 90.0)
        elbow_diff = angles.get("elbow_diff", 0.0)
        torso_tilt = angles.get("torso_tilt", 0.0)

        if elbow_diff > 25.0 and 95.0 < elbow < 150.0:
            errors.append(FormError(
                message="Press evenly",
                speech="Press up evenly with both arms.",
                severity="warning",
            ))

        if 125.0 <= elbow < 150.0 and self.prev_state in ("mid", "up"):
            errors.append(FormError(
                message="Full lockout",
                speech="Fully extend your arms at the top.",
                severity="warning",
            ))

        if torso_tilt > 0.35:
            errors.append(FormError(
                message="Keep back flat",
                speech="Keep your back flat on the bench. Don't sit up.",
                severity="warning",
            ))

        return errors

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        return angles["elbow"] <= 105.0 and abs(angles.get("torso_tilt", 0.0)) < 0.40

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="upper_body_visible_side",
                message="Lie down in side view so shoulders, elbows, and wrists are clearly visible.",
                passed_message="Upper body detected.",
                check_fn=lambda lm, h, w: (
                    max(visibility(lm, "left_shoulder"), visibility(lm, "right_shoulder")) > 0.5
                    and max(visibility(lm, "left_elbow"), visibility(lm, "right_elbow")) > 0.5
                    and max(visibility(lm, "left_wrist"), visibility(lm, "right_wrist")) > 0.5
                ),
            ),
            CalibrationCheck(
                id="bottom_position_start",
                message="Start with weights at chest level and elbows bent.",
                passed_message="Starting position locked. Get ready!",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            ),
        ]


# ─────────────────────────────────────────────────────────────
#  20. BENT-OVER ROW
#  Hip hinge hold + elbow flexion pulling load toward torso.
#  Side-view preferred. Reuses hip-hinge idea from Deadlift + pull angle.
#  Unlocks: DB Row, Barbell Row, Seated Cable Row (partial), Renegade Row (partial)
# ─────────────────────────────────────────────────────────────


class BentOverRow(BaseExercise):
    name = "bent_over_row"
    display_name = "Bent-Over Row"
    START_CUE = "Hinge at the hips, back flat, arms hanging straight down."
    MIN_REP_DURATION = 0.8
    CALIBRATION_DURATION = 2.0
    TRACKED_LANDMARKS = ["shoulder", "elbow", "wrist", "hip", "knee", "ear"]

    def __init__(self):
        super().__init__()
        self._reached_up = False

    def reset(self):
        super().reset()
        self._reached_up = False

    def _active_side(self, lm, h: int, w: int) -> str:
        left_vis = (
            visibility(lm, "left_shoulder")
            + visibility(lm, "left_elbow")
            + visibility(lm, "left_hip")
            + visibility(lm, "left_wrist")
        ) / 4.0
        right_vis = (
            visibility(lm, "right_shoulder")
            + visibility(lm, "right_elbow")
            + visibility(lm, "right_hip")
            + visibility(lm, "right_wrist")
        ) / 4.0
        return "left" if left_vis >= right_vis else "right"

    def compute_angles(self, lm, h: int, w: int) -> Dict[str, float]:
        side = self._active_side(lm, h, w)

        elbow = compute_angle(lm, f"{side}_shoulder", f"{side}_elbow", f"{side}_wrist", h, w)
        hip = compute_angle(lm, f"{side}_shoulder", f"{side}_hip", f"{side}_knee", h, w)
        spine = compute_angle(lm, f"{side}_ear", f"{side}_shoulder", f"{side}_hip", h, w)

        wrist = get_coords(lm, f"{side}_wrist", h, w)
        hip_pt = get_coords(lm, f"{side}_hip", h, w)
        shoulder = get_coords(lm, f"{side}_shoulder", h, w)
        torso = math.hypot(shoulder[0] - hip_pt[0], shoulder[1] - hip_pt[1]) + 1e-6
        wrist_to_hip = math.hypot(wrist[0] - hip_pt[0], wrist[1] - hip_pt[1]) / torso

        return {
            "elbow": elbow,
            "hip": hip,
            "spine": spine,
            "wrist_to_hip": wrist_to_hip,
            "active_side": side,
        }

    def get_fsm_state(self, angles: Dict[str, float], lm, h: int, w: int) -> str:
        elbow = angles.get("elbow", 180.0)

        if elbow <= 70.0:
            self._reached_up = True
            return "up"
        if elbow >= 145.0:
            return "down"
        return "mid"

    def should_count(self) -> bool:
        if self.current_state == "down" and self._reached_up:
            self._reached_up = False
            return True
        return False

    def check_form_errors(self, angles: Dict[str, float], lm, h: int, w: int) -> List[FormError]:
        errors = []
        hip = angles.get("hip", 180.0)
        spine = angles.get("spine", 180.0)
        elbow = angles.get("elbow", 180.0)

        if hip >= 150.0:
            errors.append(FormError(
                message="Stay hinged",
                speech="Keep your hips hinged. Don't stand up between rows.",
                severity="warning",
            ))

        if spine < 145.0:
            errors.append(FormError(
                message="Keep back flat",
                speech="Keep your back flat and chest up. Avoid rounding your spine.",
                severity="warning",
            ))

        if 70.0 < elbow <= 100.0 and self.prev_state == "mid":
            errors.append(FormError(
                message="Pull higher",
                speech="Pull your elbows back until the weight reaches your torso.",
                severity="warning",
            ))

        return errors

    def check_start_posture(self, lm, h: int, w: int) -> bool:
        angles = self.compute_angles(lm, h, w)
        return angles["hip"] <= 130.0 and angles["elbow"] >= 140.0 and angles["spine"] >= 145.0

    def get_calibration_checks(self) -> List[CalibrationCheck]:
        return [
            CalibrationCheck(
                id="full_body_visible_side",
                message="Stand in side view so shoulders, hips, elbows, and wrists are visible.",
                passed_message="Body profile detected.",
                check_fn=lambda lm, h, w: (
                    max(visibility(lm, "left_shoulder"), visibility(lm, "right_shoulder")) > 0.5
                    and max(visibility(lm, "left_hip"), visibility(lm, "right_hip")) > 0.5
                    and max(visibility(lm, "left_elbow"), visibility(lm, "right_elbow")) > 0.5
                    and max(visibility(lm, "left_wrist"), visibility(lm, "right_wrist")) > 0.5
                ),
            ),
            CalibrationCheck(
                id="hinged_arms_hanging",
                message="Hinge at the hips with a flat back and arms hanging straight down.",
                passed_message="Starting position locked. Get ready!",
                check_fn=lambda lm, h, w: self.check_start_posture(lm, h, w),
            ),
        ]

# ─────────────────────────────────────────────────────────────
#  Registry
# ─────────────────────────────────────────────────────────────

ALL_EXERCISES = {
    "squat": Squat,
    "push_up": PushUp,
    "bicep_curl": BicepCurl,
    "hammer_curl": HammerCurl,
    "shoulder_press": ShoulderPress,
    "lateral_raise": LateralRaise,
    "lunge": Lunge,
    "side_lunge": SideLunge,
    "deadlift": Deadlift,
    "glute_bridge": GluteBridge,
    "calf_raise": CalfRaise,
    "leg_raise": LegRaise,
    "plank": Plank,
    "wall_sit": WallSit,
    "jumping_jack": JumpingJack,
    "high_knees": HighKnees,
    "mountain_climber": MountainClimber,
    "tricep_dip": TricepDip,
    "horizontal_press": HorizontalPress,
    "bent_over_row": BentOverRow,
}


def get_exercise(name: str) -> BaseExercise:
    """Instantiate and return an exercise by name."""
    cls = ALL_EXERCISES.get(name)
    if cls is None:
        raise ValueError(f"Unknown exercise: {name}. Available: {list(ALL_EXERCISES.keys())}")
    return cls()
