import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class LegRaiseExercise {
  static key = "leg_raise";
  static displayName = "Leg Raise";
  static startCue = "Lie flat on your back with your legs straight.";
  static minRepDuration = 0.8;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "hip", "knee", "ankle"];
  static orientation = null;

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedUpPhase = false; this.hadBentKneeThisRep = false; this.lastCountTime = 0;
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
    };
  }
  getFsmState(a) {
    if (a.hip <= 95) { this.reachedUpPhase = true; return "up"; }
    if (a.hip >= 155) return "down";
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "down" && this.reachedUpPhase) { this.reachedUpPhase = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "down" && this.currentState !== "down") this.hadBentKneeThisRep = false;
    if (a.hip < 150 && a.knee < 155) {
      this.hadBentKneeThisRep = true;
      errors.push({ message: "Keep legs straight", speech: "Keep your knees straight and locked throughout the raise." });
    }
    return errors;
  }
  getRepQualityErrors() {
    const had = this.hadBentKneeThisRep; this.hadBentKneeThisRep = false;
    return had ? { message: "Keep legs straight", speech: "Keep your knees straight and locked throughout the raise." } : null;
  }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.hip >= 155 && a.knee >= 160;
  }
  getCalibrationChecks() {
    return [
      { id: "full_body_visible_side", message: "Lie down in side view so shoulders, hips, and feet are visible.",
        check: (lm) => maxVis(lm,"shoulder") > 0.5 && maxVis(lm,"hip") > 0.5 && maxVis(lm,"ankle") > 0.5 },
      { id: "lying_flat", message: "Lie flat on your back with legs extended straight.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}