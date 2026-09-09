import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class PushUpExercise {
  static key = "push_up";
  static displayName = "Push Up";
  static startCue = "Get into a plank position with your arms fully extended.";
  static minRepDuration = 1.0;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "elbow", "wrist", "hip", "ankle"];
  static orientation = "landscape";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedDown = false; this.hadHipDevThisRep = false; this.hipDevReason = null; this.lastCountTime = 0;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm, "left_shoulder") + visibility(lm, "left_elbow") + visibility(lm, "left_hip") + visibility(lm, "left_ankle")) / 4;
    const rightVis = (visibility(lm, "right_shoulder") + visibility(lm, "right_elbow") + visibility(lm, "right_hip") + visibility(lm, "right_ankle")) / 4;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const elbow = computeAngle(lm, `${side}_shoulder`, `${side}_elbow`, `${side}_wrist`, w, h);
    const s = px(lm, `${side}_shoulder`, w, h), hip = px(lm, `${side}_hip`, w, h), a = px(lm, `${side}_ankle`, w, h);
    const torso = dist(s, hip) + 1e-6;
    let expectedY;
    if (Math.abs(a[0] - s[0]) > 1e-3) {
      const t = (hip[0] - s[0]) / (a[0] - s[0]);
      expectedY = s[1] + t * (a[1] - s[1]);
    } else expectedY = (s[1] + a[1]) / 2;
    return { elbow, normHipDev: (hip[1] - expectedY) / torso, activeSide: side };
  }
  getFsmState(a) {
    if (a.elbow >= 155) return "up";
    if (a.elbow <= 90) { this.reachedDown = true; return "down"; }
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "up" && this.reachedDown) { this.reachedDown = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "up" && this.currentState !== "up") {
      this.hadHipDevThisRep = false; this.hipDevReason = null;
    }
    if (a.normHipDev < -0.15) {
      this.hadHipDevThisRep = true;
      this.hipDevReason = { message: "Hips too high", speech: "Lower your hips. Keep your body in a straight plank line." };
      errors.push(this.hipDevReason);
    } else if (a.normHipDev > 0.15) {
      this.hadHipDevThisRep = true;
      this.hipDevReason = { message: "Hips sagging", speech: "Engage your core. Don't let your hips drop." };
      errors.push(this.hipDevReason);
    }
    return errors;
  }
  getRepQualityErrors() {
    const had = this.hadHipDevThisRep; const reason = this.hipDevReason;
    this.hadHipDevThisRep = false; this.hipDevReason = null;
    return had ? reason : null;
  }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.elbow >= 150 && Math.abs(a.normHipDev) <= 0.15;
  }
  getCalibrationChecks() {
    return [
      { id: "full_body_visible_side", message: "Set up in side view so shoulders, hips, and ankles are visible.",
        check: (lm) => maxVis(lm, "shoulder") > 0.5 && maxVis(lm, "hip") > 0.5 && maxVis(lm, "ankle") > 0.5 },
      { id: "plank_straight", message: "Get into a plank — straight line from shoulders to ankles.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}