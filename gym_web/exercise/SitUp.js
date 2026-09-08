// ─────────────────────────────────────────────────────────────
//  SIT-UP
//  Uses the exact same shoulder->hip->knee angle as LegRaise — but
//  here the TORSO curls toward fixed legs, instead of the legs lifting
//  toward a fixed torso. Same formula, opposite segment moving; a good
//  example of why computeAngles is defined per-exercise even when the
//  underlying geometry is shared.
// ─────────────────────────────────────────────────────────────


import { computeAngle, px, dist, maxVis, visibility } from "js/landmarks.js";

export
class SitUpExercise {
  static key = "sit_up";
  static displayName = "Sit-Up";
  static startCue = "Lie on your back with knees bent, feet flat on the floor.";
  static minRepDuration = 0.8;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "hip", "knee", "ankle"];
  static orientation = null; // lying down, same as GluteBridge/LegRaise

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedUp = false; this.lastCountTime = 0;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_shoulder")+visibility(lm,"left_hip")+visibility(lm,"left_knee")+visibility(lm,"left_ankle"))/4;
    const rightVis = (visibility(lm,"right_shoulder")+visibility(lm,"right_hip")+visibility(lm,"right_knee")+visibility(lm,"right_ankle"))/4;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const hip = computeAngle(lm, `${side}_shoulder`, `${side}_hip`, `${side}_knee`, w, h);
    const knee = computeAngle(lm, `${side}_hip`, `${side}_knee`, `${side}_ankle`, w, h);
    return { hip, knee, activeSide: side };
  }
  getFsmState(a) {
    if (a.hip <= 90) { this.reachedUp = true; return "up"; }
    if (a.hip >= 160) return "down";
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "down" && this.reachedUp) { this.reachedUp = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (a.knee > 150) errors.push({ message: "Bend your knees", speech: "Keep your knees bent and feet planted to protect your lower back." });
    return errors;
  }
  getRepQualityErrors() { return null; }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.hip >= 160 && a.knee >= 70 && a.knee <= 120;
  }
  getCalibrationChecks() {
    return [
      { id: "full_body_visible_side", message: "Lie down in side view so your shoulders, hips, knees, and feet are visible.",
        check: (lm) => maxVis(lm,"shoulder")>0.5 && maxVis(lm,"hip")>0.5 && maxVis(lm,"knee")>0.5 && maxVis(lm,"ankle")>0.5 },
      { id: "knees_bent_start", message: "Lie flat with knees bent and feet planted on the floor.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
