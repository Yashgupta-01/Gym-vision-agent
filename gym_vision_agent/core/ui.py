"""
UI Renderer
All OpenCV drawing helpers: overlays, counters, timers, feedback panels.
"""

import cv2
import numpy as np
import time
from typing import Optional
from core.engine import EngineState


# Colour palette (BGR)
C_WHITE      = (255, 255, 255)
C_BLACK      = (0,   0,   0)
C_GREEN      = (0,   220, 100)
C_DARK_GREEN = (0,   160, 60)
C_RED        = (40,  40,  220)
C_ORANGE     = (0,   160, 255)
C_YELLOW     = (0,   220, 220)
C_BLUE       = (230, 100, 30)
C_DARK       = (30,  30,  30)
C_GREY       = (130, 130, 130)
C_ACCENT     = (0,   200, 255)


def _rect_alpha(frame, x1, y1, x2, y2, color, alpha=0.65):
    """Draw a filled semi-transparent rectangle."""
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


def _text(frame, text, x, y, font_scale=0.7, color=C_WHITE, thickness=2, font=cv2.FONT_HERSHEY_DUPLEX):
    cv2.putText(frame, text, (x, y), font, font_scale, C_BLACK, thickness + 2, cv2.LINE_AA)
    cv2.putText(frame, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)


def _text_centered(frame, text, cy, font_scale=1.0, color=C_WHITE, thickness=2):
    (w_text, h_text), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, font_scale, thickness)
    x = (frame.shape[1] - w_text) // 2
    _text(frame, text, x, cy, font_scale, color, thickness)


def draw_menu(frame, exercises: list, selected_idx: int):
    """Draw the exercise selection menu."""
    h, w = frame.shape[:2]
    _rect_alpha(frame, 0, 0, w, h, C_DARK, 0.75)
    _text_centered(frame, "GYM VISION AI", 60, 1.2, C_ACCENT, 2)
    _text_centered(frame, "Select Exercise  [UP/DOWN]  [ENTER to start]", 95, 0.5, C_GREY, 1)

    cols = 1 if w<500 else 2
    rows = (len(exercises) + cols - 1) // cols
    item_h = 42
    start_y = 130
    col_w = w // cols

    for i, ex in enumerate(exercises):
        row = i // cols
        col = i % cols
        x = col * col_w + 30
        y = start_y + row * item_h

        if i == selected_idx:
            _rect_alpha(frame, col * col_w + 10, y - 28, col * col_w + col_w - 10, y + 8, C_ACCENT, 0.5)
            _text(frame, f"> {ex.replace('_', ' ').title()}", x, y, 0.65, C_BLACK, 2)
        else:
            _text(frame, f"  {ex.replace('_', ' ').title()}", x, y, 0.55, C_WHITE, 1)

    _text_centered(frame, "[Q] Quit", h - 20, 0.5, C_GREY, 1)


def draw_reps_config(frame, target_reps, target_sets):
    """Draw config screen for reps/sets."""
    h, w = frame.shape[:2]
    _rect_alpha(frame, 0, 0, w, h, C_DARK, 0.80)
    _text_centered(frame, "Set Your Goal", 100, 1.0, C_ACCENT, 2)
    _text_centered(frame, f"REPS:  {target_reps}   [A / D]", 180, 0.8, C_WHITE, 2)
    _text_centered(frame, f"SETS:  {target_sets}   [W / S]", 230, 0.8, C_WHITE, 2)
    _text_centered(frame, "ENTER to confirm   ESC to go back", h - 40, 0.55, C_GREY, 1)


def draw_calibration_screen(frame, state: EngineState):
    """Overlay during initial posture check."""
    h, w = frame.shape[:2]
    held = state.calibration_remaining
    total = state.calibration_total or 2.5   # seconds; falls back if not yet set
    draw_posture_guide(frame, state.calibration_guide, ok=(state.active_calibration_check is None))

    # Progress bar
    bar_w = int(w * 0.6)
    bar_h = 22
    bx = (w - bar_w) // 2
    by = h - 80
    _rect_alpha(frame, bx - 4, by - 4, bx + bar_w + 4, by + bar_h + 4, C_DARK, 0.7)
    fill = int((1 - (held / total)) * bar_w)
    cv2.rectangle(frame, (bx, by), (bx + fill, by + bar_h), C_GREEN, -1)
    cv2.rectangle(frame, (bx, by), (bx + bar_w, by + bar_h), C_WHITE, 1)

    msg = state.message or "Hold starting position!"
    _text_centered(frame, msg, h - 100, 0.8, C_YELLOW, 2)
    _text_centered(frame, state.display_name.upper(), 55, 1.1, C_ACCENT, 2)


ZONE_COLORS = {
    "RED": C_RED,
    "YELLOW": C_YELLOW,
    "GREEN": C_GREEN,
}

def draw_feedback_border(frame, zone:str, thicknsess:int = 14):
    """Thick colored border — red (not visible), yellow (visible, not correct),
    green (correct) — mirrors ExerSights' visibility/correctness indicator."""

    h, w = frame.shape[:2]
    color = ZONE_COLORS.get(zone, C_GREY)
    cv2.rectangle(frame, (0, 0), (w-1, h-1), color, thicknsess)
    

def draw_workout_hud(frame, state: EngineState, fps: float, elapsed: float):
    """Main HUD during working phase."""
    h, w = frame.shape[:2]

    # Rep rejection banner (red, top-centered)
    if state.rep_rejected:
        _text_centered(frame, "NOT COUNTED — FIX YOUR FORM", 90, 0.8, C_RED, 2)


    # ── Left panel ────────────────────────────────────────────
    panel_w = max(160, min(200, int (w*0.22)))

    _rect_alpha(frame, 0, 0, panel_w, 300, C_DARK, 0.72)
    cv2.rectangle(frame, (0, 0), (panel_w, 300), C_ACCENT, 1)

    _text(frame, state.display_name.upper()[:16], 10, 28, 0.55, C_ACCENT, 1)
    _text(frame, "REPS", 10, 80, 0.5, C_GREY, 1)
    _text(frame, str(state.rep_count), 10, 130, 2.5, C_WHITE, 4)
    _text(frame, f"/ {state.target_reps}", 100, 130, 0.8, C_GREY, 1)

    _text(frame, "SET", 10, 165, 0.5, C_GREY, 1)
    _text(frame, f"{state.set_count} / {state.target_sets}", 10, 195, 0.85, C_WHITE, 2)

    # Form score
    score = state.form_score
    if score >= 85:
        sc = C_GREEN
    elif score >= 65:
        sc = C_YELLOW
    else:
        sc = C_RED

    _text(frame, "FORM", 10, 230, 0.5, C_GREY, 1)
    _text(frame, f"{score}%", 10, 260, 0.85, sc, 2)

    # ── Top right: timer + FPS ────────────────────────────────
    mins = int(elapsed) // 60
    secs = int(elapsed) % 60
    timer_str = f"{mins:02d}:{secs:02d}"
    _text(frame, timer_str, w - 120, 35, 0.9, C_WHITE, 2)
    _text(frame, f"FPS {fps:.0f}", w - 90, 60, 0.5, C_GREY, 1)

    # ── FSM state badge ───────────────────────────────────────
    s = (state.current_state or "").upper()
    badge_color = C_GREEN if s in ("UP", "OPEN", "HOLD", "KNEE_UP") else C_ORANGE
    _text(frame, s, w - 120, h - 20, 0.7, badge_color, 2)

    # ── Form errors (bottom) ──────────────────────────────────
    if state.form_errors:
        by = h - 60
        for err in state.form_errors[:2]:
            c = C_RED if err.severity == "error" else C_ORANGE
            _rect_alpha(frame, panel_w + 10, by - 22, w - 10, by + 4, C_DARK, 0.75)
            _text(frame, f"⚠  {err.message}", panel_w + 20, by, 0.6, c, 1)
            by -= 32


def draw_rest_screen(frame, state: EngineState):
    """Full-screen rest overlay."""
    h, w = frame.shape[:2]
    _rect_alpha(frame, 0, 0, w, h, C_DARK, 0.82)
    _text_centered(frame, "REST", h // 2 - 80, 3.0, C_ACCENT, 5)
    remaining = int(state.rest_remaining)
    _text_centered(frame, f"{remaining}s", h // 2 + 40, 2.0, C_WHITE, 4)
    _text_centered(frame, f"Next up: Set {state.set_count}  ·  {state.target_reps} reps", h // 2 + 110, 0.7, C_GREY, 1)


def draw_done_screen(frame, state: EngineState):
    """Workout complete screen."""
    h, w = frame.shape[:2]
    _rect_alpha(frame, 0, 0, w, h, (0, 60, 0), 0.88)
    _text_centered(frame, "WORKOUT COMPLETE!", h // 2 - 60, 1.2, C_GREEN, 3)
    _text_centered(frame, f"{state.target_sets} sets  ×  {state.target_reps} reps", h // 2 + 10, 0.8, C_WHITE, 2)
    _text_centered(frame, "Press ENTER to train again  |  Q to quit", h - 40, 0.55, C_GREY, 1)


def draw_posture_guide(frame, guide_data, ok: bool):
    if not guide_data or not isinstance(guide_data, dict):
        return
    if "left_x" not in guide_data or "right_x" not in guide_data:
        return
    color = C_GREEN if ok else C_RED
    h = frame.shape[0]
    try:
        left_x = int(guide_data["left_x"])
        right_x = int(guide_data["right_x"])
    except (TypeError, ValueError):
        return
    cv2.line(frame, (left_x, h), (left_x, h - 200), color, 3)
    cv2.line(frame, (right_x, h), (right_x, h - 200), color, 3)

def draw_fall_alert(frame, state: EngineState):
    """Draw a red cross over the body when a fall is detected."""
    h,w = frame.shape[:2]
    _rect_alpha(frame, 0, 0, w, h, C_RED, 0.3)
    _text_centered(frame, "ARE YOU OKAY?", h // 2 - 40, 1.3, C_YELLOW, 3)
    _text_centered(frame, "Press ENTER when ready to continue", h // 2 + 30, 0.7, C_WHITE, 2)


def draw_hold_hud(frame, state: EngineState, fps: float):
    """HUD for freeform duration-based exercises (Plank, Wall Sit) — no reps/sets,
    just current hold time and personal best for this session."""
    h, w = frame.shape[:2]
    panel_w = max(160, min(200, int (w*0.22)))

    _rect_alpha(frame, 0, 0, panel_w, 200, C_DARK, 0.72)
    cv2.rectangle(frame, (0, 0), (panel_w, 200), C_ACCENT, 1)

    _text(frame, state.display_name.upper()[:16], 10, 28, 0.55, C_ACCENT, 1)
    _text(frame, "CURRENT HOLD", 10, 70, 0.5, C_GREY, 1)
    _text(frame, f"{state.hold_current:.1f}s", 10, 115, 1.4, C_WHITE, 3)
    _text(frame, "BEST", 10, 150, 0.5, C_GREY, 1)
    _text(frame, f"{state.hold_best:.1f}s", 10, 185, 0.9, C_GREEN, 2)

    _text(frame, f"FPS {fps:.0f}", w - 90, 30, 0.5, C_GREY, 1)
    _text_centered(frame, "Press Q to finish", h - 20, 0.5, C_GREY, 1)