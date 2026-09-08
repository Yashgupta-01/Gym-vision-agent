// ─────────────────────────────────────────────────────────────
//  OVERHEAD TRICEP EXTENSION
//  Standing, weight held overhead. Elbow angle FSM (same shape as
//  TricepDip), plus an elbow-drift check reused from BicepCurl's
//  pattern — the upper arm should stay fixed pointing up; only the
//  forearm should move.
// ─────────────────────────────────────────────────────────────

import { computeAngle, px, dist, maxVis, visibility } from "js/landmarks.js";
export class OverheadTricepExtensionExercise {
  static key = "overhead_tricep_extension";
  static displayName = "Overhead Tricep Extension";
  static startCue = "Hold the weight straight overhead, arm fully extended.";
  static minRepDuration = 0.8;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "elbow", "wrist"];
  static orientation = "portrait";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedDown = false; this.hadElbowDriftThisRep = false; this.lastCountTime = 0;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_shoulder")+visibility(lm,"left_elbow")+visibility(lm,"left_wrist"))/3;
    const rightVis = (visibility(lm,"right_shoulder")+visibility(lm,"right_elbow")+visibility(lm,"right_wrist"))/3;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const elbow = computeAngle(lm, `${side}_shoulder`, `${side}_elbow`, `${side}_wrist`, w, h);
    const s = px(lm, `${side}_shoulder`, w, h), e = px(lm, `${side}_elbow`, w, h);
    const upperArm = dist(s, e) + 1e-6;
    const elbowDrift = Math.abs(e[0] - s[0]) / upperArm;
    return { elbow, elbowDrift, activeSide: side };
  }
  getFsmState(a) {
    if (a.elbow >= 160) return "up";
    if (a.elbow <= 70) { this.reachedDown = true; return "down"; }
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "up" && this.reachedDown) { this.reachedDown = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "up" && this.currentState !== "up") this.hadElbowDriftThisRep = false;
    if (a.elbowDrift > 0.35 && a.elbow < 150) {
      this.hadElbowDriftThisRep = true;
      errors.push({ message: "Elbow drifting", speech: "Keep your upper arm still, only your forearm should move." });
    }
    return errors;
  }
  getRepQualityErrors() {
    const had = this.hadElbowDriftThisRep; this.hadElbowDriftThisRep = false;
    return had ? { message: "Elbow drifting", speech: "Keep your upper arm still, only your forearm should move." } : null;
  }
  checkStartPosture(lm, w, h) { return this.computeAngles(lm, w, h).elbow >= 150; }
  getCalibrationChecks() {
    return [
      { id: "upper_body_visible", message: "Step back so your shoulder, elbow, and wrist are visible.",
        check: (lm) => maxVis(lm,"shoulder")>0.5 && maxVis(lm,"elbow")>0.5 && maxVis(lm,"wrist")>0.5 },
      { id: "arm_overhead_start", message: "Hold the weight straight overhead with your arm fully extended.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}