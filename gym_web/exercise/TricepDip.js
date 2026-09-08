import { computeAngle, px, dist, maxVis, visibility } from "js/landmarks.js";

export class TricepDipExercise {
  static key = "tricep_dip";
  static displayName = "Tricep Dip";
  static startCue = "Sit on edge of chair/bench with arms fully extended.";
  static minRepDuration = 0.8;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "elbow", "wrist"];
  static orientation = "landscape";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedDown = false; this.lastCountTime = 0;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_shoulder")+visibility(lm,"left_elbow")+visibility(lm,"left_wrist"))/3;
    const rightVis = (visibility(lm,"right_shoulder")+visibility(lm,"right_elbow")+visibility(lm,"right_wrist"))/3;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const elbow = computeAngle(lm, `${side}_shoulder`, `${side}_elbow`, `${side}_wrist`, w, h);
    const ls = px(lm, `${side}_shoulder`, w, h), le = px(lm, `${side}_elbow`, w, h);
    const upperArm = dist(ls, le) + 1e-6;
    return { elbow, elbowFlareRatio: Math.abs(le[0] - ls[0]) / upperArm };
  }
  getFsmState(a) {
    if (a.elbow >= 150) return "up";
    if (a.elbow <= 95) { this.reachedDown = true; return "down"; }
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "up" && this.reachedDown) { this.reachedDown = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (a.elbow > 95 && a.elbow <= 115 && this.prevState !== "up")
      errors.push({ message: "Dip lower", speech: "Dip lower until your elbows are at a 90-degree angle." });
    if (a.elbowFlareRatio > 0.8)
      errors.push({ message: "Keep elbows tucked", speech: "Keep your elbows tucked back close to your body." });
    return errors;
  }
  getRepQualityErrors() { return null; }
  checkStartPosture(lm, w, h) { return this.computeAngles(lm, w, h).elbow >= 150; }
  getCalibrationChecks() {
    return [
      { id: "upper_body_visible", message: "Position camera in side view so shoulders, elbows, and wrists are clear.",
        check: (lm) => maxVis(lm,"shoulder")>0.5 && maxVis(lm,"elbow")>0.5 && maxVis(lm,"wrist")>0.5 },
      { id: "arm_lockout", message: "Support yourself with arms fully straight.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
