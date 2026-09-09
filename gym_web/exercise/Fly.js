// ─────────────────────────────────────────────────────────────
//  FLY
//  Lying position, arms open wide (T position) closing together above
//  the chest. Same hip->shoulder->elbow angle family as LateralRaise/
//  BentOverRow, but the exercise "opens" then "closes" (Squat/PushUp/
//  BenchPress start/end pattern) rather than LateralRaise's down/up.
// ─────────────────────────────────────────────────────────────

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
    this.reachedClosed = false; this.lastCountTime = 0;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_shoulder")+visibility(lm,"left_elbow")+visibility(lm,"left_wrist"))/3;
    const rightVis = (visibility(lm,"right_shoulder")+visibility(lm,"right_elbow")+visibility(lm,"right_wrist"))/3;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    // Arm-arc angle: hip->shoulder->elbow. Wide open (T position) reads
    // high; arms brought together above the chest reads low.
    const armAngle = computeAngle(lm, `${side}_hip`, `${side}_shoulder`, `${side}_elbow`, w, h);
    // A fly keeps a fixed, soft elbow bend throughout — if the elbow
    // straightens out, the movement has drifted into a press instead.
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
    if (a.elbow > 175) errors.push({ message: "Soften your elbows", speech: "Keep a slight bend in your elbows, don't lock them straight." });
    else if (a.elbow < 130) errors.push({ message: "Too much elbow bend", speech: "You're pressing, not flying. Keep your elbows fixed at a slight bend." });
    return errors;
  }
  getRepQualityErrors() { return null; }
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