// ─────────────────────────────────────────────────────────────
//  BENT-OVER ROW
//  Side-view, hip-hinge position. New geometry not used elsewhere
//  in the file: tracks the elbow's travel path (hip->shoulder->elbow)
//  rather than the wrist, since grip/handle width varies (dumbbell vs
//  barbell vs cable) but the elbow's arc stays consistent. Also adds
//  a live torso-stability check against a baseline hip-hinge angle
//  captured at the start of the set — catches the common "standing up
//  to heave the weight" cheat, which no existing exercise checks for.
// ─────────────────────────────────────────────────────────────
import { computeAngle, px, dist, maxVis, visibility } from "js/landmarks.js";

export class BentOverRowExercise {
  static key = "bent_over_row";
  static displayName = "Bent-Over Row";
  static startCue = "Hinge at your hips, torso angled forward, arms hanging straight down.";
  static minRepDuration = 0.8;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "elbow", "hip", "knee"];
  static orientation = "landscape"; // side view, same as Deadlift/MountainClimber

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedUp = false; this.hadTorsoRiseThisRep = false; this.lastCountTime = 0;
    // Captured on the first WORKING-phase frame, not during calibration —
    // simpler than hooking into the engine's calibration flag (the way
    // calf_raise's adaptive baseline needs a special-cased engine hook).
    this.baselineHipAngle = null;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_shoulder")+visibility(lm,"left_elbow")+visibility(lm,"left_hip"))/3;
    const rightVis = (visibility(lm,"right_shoulder")+visibility(lm,"right_elbow")+visibility(lm,"right_hip"))/3;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    // Arm-pull angle: hip->shoulder->elbow. Near 180 when the arm hangs
    // straight down in line with the torso (bottom of the row); shrinks
    // toward ~45-60 as the elbow drives up and back past the torso line
    // (top of the row).
    const armPull = computeAngle(lm, `${side}_hip`, `${side}_shoulder`, `${side}_elbow`, w, h);
    // Hip-hinge angle: shoulder->hip->knee. Should stay roughly constant
    // throughout the set — a big live deviation from the baseline means
    // the torso is standing up to heave the weight instead of the arm
    // doing the work.
    const hipHinge = computeAngle(lm, `${side}_shoulder`, `${side}_hip`, `${side}_knee`, w, h);
    return { armPull, hipHinge, activeSide: side };
  }
  getFsmState(a) {
    if (this.baselineHipAngle === null) this.baselineHipAngle = a.hipHinge;
    if (a.armPull >= 150) return "down";
    if (a.armPull <= 60) { this.reachedUp = true; return "up"; }
    return "mid";
  }
  shouldCount() {
    // Rep starts and ends at full arm extension ("down"), mirroring the
    // BicepCurl pattern (starts/ends at extension, not contraction).
    if (this.currentState === "down" && this.reachedUp) { this.reachedUp = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "down" && this.currentState !== "down") this.hadTorsoRiseThisRep = false;
    if (this.baselineHipAngle !== null && (a.hipHinge - this.baselineHipAngle) > 20) {
      this.hadTorsoRiseThisRep = true;
      errors.push({ message: "Torso rising", speech: "Keep your torso still, don't stand up to heave the weight." });
    } else if (a.armPull <= 90 && a.armPull > 60) {
      errors.push({ message: "Pull higher", speech: "Pull your elbow further back until it passes your torso." });
    }
    return errors;
  }
  getRepQualityErrors() {
    const had = this.hadTorsoRiseThisRep; this.hadTorsoRiseThisRep = false;
    return had ? { message: "Torso rising", speech: "Keep your torso still, don't stand up to heave the weight." } : null;
  }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.armPull >= 150 && a.hipHinge >= 45 && a.hipHinge <= 100;
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