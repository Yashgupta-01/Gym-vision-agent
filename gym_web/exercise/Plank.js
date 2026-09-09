import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class PlankExercise {
  static key = "plank";
  static displayName = "Plank";
  static isDurationBased = true;
  static startCue = "Maintain a straight line from shoulders to ankles.";
  static minRepDuration = 5.0;
  static calibrationDuration = 2.5;
  static trackedLandmarks = ["shoulder", "hip", "ankle"];
  static orientation = "landscape";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.holdStartTime = 0; this.wasHolding = false; this.lastCountTime = 0;
    this._currentTime = 0;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_shoulder")+visibility(lm,"left_hip")+visibility(lm,"left_ankle"))/3;
    const rightVis = (visibility(lm,"right_shoulder")+visibility(lm,"right_hip")+visibility(lm,"right_ankle"))/3;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const s = px(lm, `${side}_shoulder`, w, h), hip = px(lm, `${side}_hip`, w, h), a = px(lm, `${side}_ankle`, w, h);
    const bodyLine = computeAngle(lm, `${side}_shoulder`, `${side}_hip`, `${side}_ankle`, w, h);
    const torso = dist(s, hip) + 1e-6;
    let expectedY;
    if (Math.abs(a[0] - s[0]) > 1e-3) {
      const t = (hip[0] - s[0]) / (a[0] - s[0]);
      expectedY = s[1] + t * (a[1] - s[1]);
    } else expectedY = (s[1] + a[1]) / 2;
    return { bodyLine, normHipDev: (hip[1] - expectedY) / torso };
  }
  getFsmState(a) {
    if (a.bodyLine >= 160 && a.bodyLine <= 180 && Math.abs(a.normHipDev) <= 0.12) {
      if (!this.wasHolding) { this.holdStartTime = this._currentTime; this.wasHolding = true; }
      return "hold";
    }
    this.wasHolding = false;
    return "break";
  }
  shouldCount() {
    if (this.prevState === "hold" && this.currentState === "break")
      return (this._currentTime - this.holdStartTime) >= this.constructor.minRepDuration;
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (a.normHipDev < -0.12) errors.push({ message: "Hips too high", speech: "Lower your hips into a straight plank position." });
    else if (a.normHipDev > 0.12) errors.push({ message: "Hips sagging", speech: "Engage your core and lift your hips." });
    return errors;
  }
  getRepQualityErrors() { return null; }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.bodyLine >= 160 && a.bodyLine <= 180 && Math.abs(a.normHipDev) <= 0.12;
  }
  getCalibrationChecks() {
    return [
      { id: "full_body_visible", message: "Position camera in side view so shoulders, hips, and feet are visible.",
        check: (lm) => maxVis(lm,"shoulder")>0.5 && maxVis(lm,"hip")>0.5 && maxVis(lm,"ankle")>0.5 },
      { id: "plank_hold_start", message: "Get into a straight plank and hold still.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
