//  TRICEP KICKBACK
//  Bent-over position, upper arm fixed parallel to torso. Elbow-angle
//  FSM (extension/contraction, same start/end pattern as BicepCurl),
//  plus a stability check on the upper-arm angle — reuses the baseline
//  pattern from BentOverRow/RearDeltFly, applied to the upper arm
//  instead of the torso.
// ─────────────────────────────────────────────────────────────

import { computeAngle, px, dist, maxVis, visibility } from "js/landmarks.js";

export class TricepKickbackExercise {
  static key = "tricep_kickback";
  static displayName = "Tricep Kickback";
  static startCue = "Hinge forward, upper arm raised parallel to your torso, elbow bent.";
  static minRepDuration = 0.6;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "elbow", "wrist", "hip"];
  static orientation = "landscape";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedUp = false; this.hadArmDropThisRep = false; this.lastCountTime = 0;
    this.baselineArmAngle = null;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_shoulder")+visibility(lm,"left_elbow")+visibility(lm,"left_wrist"))/3;
    const rightVis = (visibility(lm,"right_shoulder")+visibility(lm,"right_elbow")+visibility(lm,"right_wrist"))/3;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const elbow = computeAngle(lm, `${side}_shoulder`, `${side}_elbow`, `${side}_wrist`, w, h);
    const armAngle = computeAngle(lm, `${side}_hip`, `${side}_shoulder`, `${side}_elbow`, w, h);
    return { elbow, armAngle, activeSide: side };
  }
  getFsmState(a) {
    if (this.baselineArmAngle === null) this.baselineArmAngle = a.armAngle;
    if (a.elbow <= 100) return "down";
    if (a.elbow >= 150) { this.reachedUp = true; return "up"; }
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "down" && this.reachedUp) { this.reachedUp = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "down" && this.currentState !== "down") this.hadArmDropThisRep = false;
    if (this.baselineArmAngle !== null && Math.abs(a.armAngle - this.baselineArmAngle) > 20) {
      this.hadArmDropThisRep = true;
      errors.push({ message: "Upper arm dropping", speech: "Keep your upper arm still and raised, only swing your forearm." });
    }
    return errors;
  }
  getRepQualityErrors() {
    const had = this.hadArmDropThisRep; this.hadArmDropThisRep = false;
    return had ? { message: "Upper arm dropping", speech: "Keep your upper arm still and raised, only swing your forearm." } : null;
  }
  checkStartPosture(lm, w, h) { return this.computeAngles(lm, w, h).elbow <= 110; }
  getCalibrationChecks() {
    return [
      { id: "upper_body_visible_side", message: "Set up in side view so your shoulder, elbow, and wrist are visible.",
        check: (lm) => maxVis(lm,"shoulder")>0.5 && maxVis(lm,"elbow")>0.5 && maxVis(lm,"wrist")>0.5 },
      { id: "elbow_bent_start", message: "Hinge forward with your upper arm raised and elbow bent to about 90 degrees.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
