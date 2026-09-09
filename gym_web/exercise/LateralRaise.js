import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class LateralRaiseExercise {
  static key = "lateral_raise";
  static displayName = "Lateral Raise";
  static startCue = "Arms relaxed, down by your sides.";
  static minRepDuration = 0.8;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["hip", "shoulder", "wrist"];
  static orientation = "portrait";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedUp = false; this.hadHandsCloseThisRep = false; this.lastCountTime = 0;
  }
  computeAngles(lm, w, h) {
    return {
      leftRaise: computeAngle(lm, "left_hip", "left_shoulder", "left_wrist", w, h),
      rightRaise: computeAngle(lm, "right_hip", "right_shoulder", "right_wrist", w, h),
    };
  }
  getFsmState(a) {
    const avg = (a.leftRaise + a.rightRaise) / 2;
    if (avg < 40) return "down";
    if (avg >= 75) { this.reachedUp = true; return "up"; }
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "down" && this.reachedUp) { this.reachedUp = false; return true; }
    return false;
  }
  checkFormErrors(a, lm, w, h) {
    const errors = [];
    if (this.prevState === "down" && this.currentState !== "down") this.hadHandsCloseThisRep = false;
    const avg = (a.leftRaise + a.rightRaise) / 2;
    if (avg > 60 && avg <= 74 && this.prevState === "mid")
      errors.push({ message: "Raise higher", speech: "Raise your arms to shoulder height." });
    if (lm && (this.currentState === "mid" || this.currentState === "up")) {
      const lw = px(lm, "left_wrist", w, h), rw = px(lm, "right_wrist", w, h);
      const ls = px(lm, "left_shoulder", w, h), rs = px(lm, "right_shoulder", w, h);
      if (Math.abs(lw[0] - rw[0]) < Math.abs(ls[0] - rs[0]) * 1.4) {
        this.hadHandsCloseThisRep = true;
        errors.push({ message: "Hands too close", speech: "Expand your arms out to your sides." });
      }
    }
    return errors;
  }
  getRepQualityErrors() {
    const had = this.hadHandsCloseThisRep; this.hadHandsCloseThisRep = false;
    return had ? { message: "Hands too close", speech: "Expand your arms out to your sides." } : null;
  }
  checkStartPosture(lm, w, h) {
    return computeAngle(lm, "left_hip", "left_shoulder", "left_wrist", w, h) < 40;
  }
  getCalibrationChecks() {
    return [
      { id: "upper_body_visible", message: "Step back so your upper body is visible.",
        check: (lm) => maxVis(lm,"shoulder") > 0.4 },
      { id: "arms_down", message: "Arms relaxed down by your sides.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
