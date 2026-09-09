//  RUSSIAN TWIST
//  Genuinely new measurement type for this file: position-based, not
//  angle-based. Torso rotation isn't a joint angle MediaPipe's 2D
//  landmarks capture directly — approximated as how far the wrist
//  midpoint has swung sideways from the hip midline, normalized by
//  shoulder width. Flagged as needing live sensitivity tuning before
//  trusting it to distinguish a real twist from hand wobble.
// ─────────────────────────────────────────────────────────────

import { px, dist, maxVis } from "../js/landmarks.js";

export
class RussianTwistExercise {
  static key = "russian_twist";
  static displayName = "Russian Twist";
  static startCue = "Sit with knees bent, lean back slightly, hands centered in front of you.";
  static minRepDuration = 0.4;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["hip", "shoulder", "wrist"];
  static orientation = "portrait";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedRight = false; this.lastCountTime = 0;
  }
  computeAngles(lm, w, h) {
    const lw = px(lm,"left_wrist",w,h), rw = px(lm,"right_wrist",w,h);
    const lh = px(lm,"left_hip",w,h), rh = px(lm,"right_hip",w,h);
    const ls = px(lm,"left_shoulder",w,h), rs = px(lm,"right_shoulder",w,h);
    const wristMidX = (lw[0]+rw[0])/2;
    const hipMidX = (lh[0]+rh[0])/2;
    const shoulderWidth = dist(ls, rs) + 1e-6;
    const twistOffset = (wristMidX - hipMidX) / shoulderWidth;
    return { twistOffset };
  }
  getFsmState(a) {
    if (a.twistOffset <= -0.5) return "left";
    if (a.twistOffset >= 0.5) { this.reachedRight = true; return "right"; }
    return "center";
  }
  shouldCount() {
    // One full left-right-left cycle = one rep, same single-cycle
    // convention used by every other exercise in the file.
    if (this.currentState === "left" && this.reachedRight) { this.reachedRight = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    // Intentionally empty: whether the chest stays open through the
    // twist (vs. slouching) isn't reliably readable from 2D wrist/hip
    // position alone. Left blank rather than faked with a low-confidence
    // check that would generate noisy, untrustworthy cues.
    return [];
  }
  getRepQualityErrors() { return null; }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return Math.abs(a.twistOffset) < 0.25;
  }
  getCalibrationChecks() {
    return [
      { id: "upper_body_visible_frontal", message: "Face the camera so your hips, shoulders, and hands are visible.",
        check: (lm) => maxVis(lm,"hip")>0.5 && maxVis(lm,"shoulder")>0.5 && maxVis(lm,"wrist")>0.5 },
      { id: "centered_start", message: "Start with your hands centered in front of you.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
