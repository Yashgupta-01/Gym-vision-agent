import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class FlyExercise {
  static key = "fly";
  static displayName = "Dumbbell Fly";
  static startCue = "Lie back with arms open wide to your sides, elbows slightly bent.";
  static minRepDuration = 1.0;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "elbow", "wrist", "hip"];
  static orientation = "landscape";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedClosed = false; this.hadElbowFormThisRep = false; this.elbowReason = null; this.lastCountTime = 0;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_shoulder")+visibility(lm,"left_elbow")+visibility(lm,"left_wrist"))/3;
    const rightVis = (visibility(lm,"right_shoulder")+visibility(lm,"right_elbow")+visibility(lm,"right_wrist"))/3;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const armAngle = computeAngle(lm, `${side}_hip`, `${side}_shoulder`, `${side}_elbow`, w, h);
    const elbow = computeAngle(lm, `${side}_shoulder`, `${side}_elbow`, `${side}_wrist`, w, h);
    return { armAngle, elbow, activeSide: side };
  }
  getFsmState(a) {
    if (a.armAngle >= 70) return "open";
    if (a.armAngle <= 25) { this.reachedClosed = true; return "closed"; }
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "open" && this.reachedClosed) { this.reachedClosed = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "open" && this.currentState !== "open") {
      this.hadElbowFormThisRep = false; this.elbowReason = null;
    }
    if (a.elbow > 175) {
      this.hadElbowFormThisRep = true;
      this.elbowReason = { message: "Soften your elbows", speech: "Keep a slight bend in your elbows, don't lock them straight." };
      errors.push(this.elbowReason);
    } else if (a.elbow < 130) {
      this.hadElbowFormThisRep = true;
      this.elbowReason = { message: "Too much elbow bend", speech: "You're pressing, not flying. Keep your elbows fixed at a slight bend." };
      errors.push(this.elbowReason);
    }
    return errors;
  }
  getRepQualityErrors() {
    const had = this.hadElbowFormThisRep; const reason = this.elbowReason;
    this.hadElbowFormThisRep = false; this.elbowReason = null;
    return had ? reason : null;
  }
  checkStartPosture(lm, w, h) { return this.computeAngles(lm, w, h).armAngle >= 70; }
  getCalibrationChecks() {
    return [
      { id: "upper_body_visible", message: "Set up so your shoulder, elbow, and wrist are visible.",
        check: (lm) => maxVis(lm,"shoulder")>0.5 && maxVis(lm,"elbow")>0.5 && maxVis(lm,"wrist")>0.5 },
      { id: "arms_open_start", message: "Start with your arms open wide to your sides, elbows softly bent.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}