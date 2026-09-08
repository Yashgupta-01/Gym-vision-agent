"""
Pose Estimation Module
Wraps MediaPipe Pose and exposes angle utilities.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, List, Tuple


# MediaPipe landmark index map
LANDMARK_MAP = {
    "nose": 0,
    "left_ear": 7,
    "right_ear": 8,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
    "left_heel": 29,
    "right_heel": 30,
    "left_foot_index": 31,
    "right_foot_index": 32,
}


def angle_between(a: Tuple, b: Tuple, c: Tuple) -> float:
    """Return angle at point b formed by a-b-c (degrees)."""
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return float(np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0))))


def get_coords(landmarks, name: str, h: int, w: int) -> Tuple[int, int]:
    """Get pixel coordinates for a named landmark."""
    idx = LANDMARK_MAP[name]
    lm = landmarks[idx]
    return int(lm.x * w), int(lm.y * h)


def get_normalized(landmarks, name: str):
    """Get normalized (0-1) x, y for a landmark."""
    idx = LANDMARK_MAP[name]
    lm = landmarks[idx]
    return lm.x, lm.y


def visibility(landmarks, name: str) -> float:
    """Return visibility score (0-1) for a landmark."""
    idx = LANDMARK_MAP[name]
    return landmarks[idx].visibility


def compute_angle(landmarks, p1: str, p2: str, p3: str, h: int, w: int) -> float:
    """Compute angle at p2 formed by p1-p2-p3."""
    a = get_coords(landmarks, p1, h, w)
    b = get_coords(landmarks, p2, h, w)
    c = get_coords(landmarks, p3, h, w)
    return angle_between(a, b, c)


class PoseEstimator:
    """Thin wrapper around MediaPipe Pose."""

    def __init__(self, model_complexity: int = 1):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            enable_segmentation=False,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.55,
        )


    def process(self, frame):
        """
        Process a BGR frame and return MediaPipe results.
        Also draws the full skeleton on the frame (in-place).
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.pose.process(rgb)
        rgb.flags.writeable = True

        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style(),
            )
        return results

    def close(self):
        self.pose.close()
