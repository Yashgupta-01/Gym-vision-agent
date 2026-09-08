// ─────────────────────────────────────────────────────────────
//  REAR DELT FLY
//  Reuses BentOverRow's two angles (arm-raise + hip-hinge stability),
//  but the arm moves out to the SIDE here instead of pulling straight
//  back to the torso. See the reliability flag at the top of this file.
// ─────────────────────────────────────────────────────────────

import { computeAngle, px, dist, maxVis, visibility } from "js/landmarks.js";

export class RearDeltFlyExercise {
  static key = "rear_delt_fly";
  static displayName = "Rear Delt Fly";
  static startCue = "Hinge forward at your hips, arms hanging straight down.";
  static minRepDuration = 0.8;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["hip", "shoulder", "elbow", "knee"];
  static orientation = "landscape";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedUp = false; this.lastCountTime = 0;
    this.baselineHipAngle = null;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_shoulder")+visibility(lm,"left_elbow")+visibility(lm,"left_hip"))/3;
    const rightVis = (visibility(lm,"right_shoulder")+visibility(lm,"right_elbow")+visibility(lm,"right_hip"))/3;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const armRaise = computeAngle(lm, `${side}_hip`, `${side}_shoulder`, `${side}_elbow`, w, h);
    const hipHinge = computeAngle(lm, `${side}_shoulder`, `${side}_hip`, `${side}_knee`, w, h);
    return { armRaise, hipHinge, activeSide: side };
  }
  getFsmState(a) {
    if (this.baselineHipAngle === null) this.baselineHipAngle = a.hipHinge;
    if (a.armRaise >= 150) return "down";
    if (a.armRaise <= 90) { this.reachedUp = true; return "up"; }
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "down" && this.reachedUp) { this.reachedUp = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.baselineHipAngle !== null && (a.hipHinge - this.baselineHipAngle) > 20)
      errors.push({ message: "Torso rising", speech: "Keep your torso still and hinged forward, don't stand up to swing the weight." });
    return errors;
  }
  getRepQualityErrors() { return null; }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.armRaise >= 150 && a.hipHinge >= 45 && a.hipHinge <= 100;
  }
  getCalibrationChecks() {
    return [
      { id: "upper_body_visible_side", message: "Set up in side view so your shoulder, hip, and knee are visible.",
        check: (lm) => maxVis(lm,"shoulder")>0.5 && maxVis(lm,"hip")>0.5 && maxVis(lm,"knee")>0.5 },
      { id: "hinge_start", message: "Hinge forward at your hips with your arms hanging straight down.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}