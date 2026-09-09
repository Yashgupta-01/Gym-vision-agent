import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class FrontRaiseExercise {
  static key = "front_raise";
  static displayName = "Front Raise";
  static startCue = "Arms relaxed, dumbbells resting in front of your thighs.";
  static minRepDuration = 0.8;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["hip", "shoulder", "wrist"];
  static orientation = "landscape";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedUp = false; this.hadOverSwingThisRep = false; this.lastCountTime = 0;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_shoulder")+visibility(lm,"left_wrist")+visibility(lm,"left_hip"))/3;
    const rightVis = (visibility(lm,"right_shoulder")+visibility(lm,"right_wrist")+visibility(lm,"right_hip"))/3;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const raise = computeAngle(lm, `${side}_hip`, `${side}_shoulder`, `${side}_wrist`, w, h);
    return { raise, activeSide: side };
  }
  getFsmState(a) {
    if (a.raise < 40) return "down";
    if (a.raise >= 80) { this.reachedUp = true; return "up"; }
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "down" && this.reachedUp) { this.reachedUp = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "down" && this.currentState !== "down") this.hadOverSwingThisRep = false;
    if (a.raise > 95) {
      this.hadOverSwingThisRep = true;
      errors.push({ message: "Raise controlled", speech: "Don't swing past shoulder height, control the weight on the way down too." });
    } else if (a.raise > 60 && a.raise < 79 && this.prevState === "mid")
      errors.push({ message: "Raise higher", speech: "Raise the dumbbells until your arms are level with your shoulders." });
    return errors;
  }
  getRepQualityErrors() {
    const had = this.hadOverSwingThisRep; this.hadOverSwingThisRep = false;
    return had ? { message: "Raise controlled", speech: "Don't swing past shoulder height, control the weight on the way down too." } : null;
  }
  checkStartPosture(lm, w, h) {
    const side = this._activeSide(lm);
    return computeAngle(lm, `${side}_hip`, `${side}_shoulder`, `${side}_wrist`, w, h) < 40;
  }
  getCalibrationChecks() {
    return [
      { id: "upper_body_visible_side", message: "Set up in side view so your hip, shoulder, and wrist are visible.",
        check: (lm) => maxVis(lm,"hip")>0.5 && maxVis(lm,"shoulder")>0.5 && maxVis(lm,"wrist")>0.5 },
      { id: "arms_down_start", message: "Start with your arms relaxed down in front of your thighs.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}