import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class DeadliftExercise {
  static key = "deadlift";
  static displayName = "Deadlift";
  static startCue = "Stand upright with shoulders back and hips fully extended.";
  static minRepDuration = 1.0;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "hip", "knee", "ankle", "ear"];
  static orientation = "landscape";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedDown = false; this.lastCountTime = 0;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_shoulder")+visibility(lm,"left_hip")+visibility(lm,"left_knee")+visibility(lm,"left_ankle"))/4;
    const rightVis = (visibility(lm,"right_shoulder")+visibility(lm,"right_hip")+visibility(lm,"right_knee")+visibility(lm,"right_ankle"))/4;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    return {
      hip: computeAngle(lm, `${side}_shoulder`, `${side}_hip`, `${side}_knee`, w, h),
      knee: computeAngle(lm, `${side}_hip`, `${side}_knee`, `${side}_ankle`, w, h),
      spine: computeAngle(lm, `${side}_ear`, `${side}_shoulder`, `${side}_hip`, w, h),
      activeSide: side,
    };
  }
  getFsmState(a) {
    if (a.hip >= 160) return "up";
    if (a.hip <= 100) { this.reachedDown = true; return "down"; }
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "up" && this.reachedDown) { this.reachedDown = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (a.spine < 145) errors.push({ message: "Keep back straight", speech: "Keep your back flat and chest up. Avoid rounding your spine." });
    if (a.hip <= 120 && a.knee < 85) errors.push({ message: "Hinge at hips", speech: "Hinge at your hips rather than squatting down." });
    return errors;
  }
  getRepQualityErrors() { return null; }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.hip >= 160 && a.knee >= 160;
  }
  getCalibrationChecks() {
    return [
      { id: "full_body_visible_side", message: "Position camera in side view so shoulders, hips, knees, and ankles are visible.",
        check: (lm) => maxVis(lm,"shoulder")>0.5 && maxVis(lm,"hip")>0.5 && maxVis(lm,"knee")>0.5 && maxVis(lm,"ankle")>0.5 },
      { id: "standing_lockout", message: "Stand tall with back straight and hips fully extended.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}