import { computeAngle, px, dist, maxVis } from "/js/landmarks.js";

export class LungeExercise {
  static key = "lunge";
  static displayName = "Lunge";
  static startCue = "Stand tall with legs straight.";
  static minRepDuration = 0.8;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["hip", "knee", "ankle", "shoulder"];
  static orientation = "portrait";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedDown = false; this.lastCountTime = 0;
  }
  computeAngles(lm, w, h) {
    return {
      leftKnee: computeAngle(lm, "left_hip", "left_knee", "left_ankle", w, h),
      rightKnee: computeAngle(lm, "right_hip", "right_knee", "right_ankle", w, h),
    };
  }
  getFsmState(a) {
    const knee = Math.min(a.leftKnee, a.rightKnee);
    if (knee > 155) return "up";
    if (knee <= 100) { this.reachedDown = true; return "down"; }
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "up" && this.reachedDown) { this.reachedDown = false; return true; }
    return false;
  }
  checkFormErrors(a, lm, w, h) {
    const errors = [];
    if (!lm) return errors;
    const lk = px(lm, "left_knee", w, h), la = px(lm, "left_ankle", w, h);
    const ls = px(lm, "left_shoulder", w, h), rs = px(lm, "right_shoulder", w, h);
    const shoulderWidth = Math.abs(ls[0] - rs[0]) + 1e-6;
    if (Math.abs(lk[0] - la[0]) / shoulderWidth > 0.35)
      errors.push({ message: "Knee over toe", speech: "Keep your front knee aligned over your ankle." });
    return errors;
  }
  getRepQualityErrors() { return null; }
  checkStartPosture(lm, w, h) {
    return computeAngle(lm, "left_hip", "left_knee", "left_ankle", w, h) > 155;
  }
  getCalibrationChecks() {
    return [
      { id: "full_body_visible", message: "Step back so your full body is visible.",
        check: (lm) => maxVis(lm,"shoulder") > 0.4 && maxVis(lm,"ankle") > 0.4 },
      { id: "standing_straight", message: "Stand tall with both legs straight.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
