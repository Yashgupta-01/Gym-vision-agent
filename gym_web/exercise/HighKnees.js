import { computeAngle, px, dist, maxVis, visibility } from "js/landmarks.js";

export class HighKneesExercise {
  static key = "high_knees";
  static displayName = "High Knees";
  static startCue = "Stand tall with legs straight and arms at your side.";
  static minRepDuration = 0.3;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "hip", "knee", "ankle"];
  static orientation = "portrait";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedKneeUp = false; this.hadShallowThisRep = false; this.lastCountTime = 0;
  }
  computeAngles(lm, w, h) {
    const leftHip = computeAngle(lm, "left_shoulder", "left_hip", "left_knee", w, h);
    const rightHip = computeAngle(lm, "right_shoulder", "right_hip", "right_knee", w, h);
    return { leftHip, rightHip, activeHip: Math.min(leftHip, rightHip) };
  }
  getFsmState(a) {
    if (a.activeHip <= 95) { this.reachedKneeUp = true; return "knee_up"; }
    if (a.leftHip >= 150 && a.rightHip >= 150) return "down";
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "down" && this.reachedKneeUp) { this.reachedKneeUp = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "down" && this.currentState !== "down") this.hadShallowThisRep = false;
    if (a.activeHip > 95 && a.activeHip <= 120) {
      this.hadShallowThisRep = true;
      errors.push({ message: "Lift knees higher", speech: "Drive your knees up higher until your thighs are parallel to the floor." });
    }
    return errors;
  }
  getRepQualityErrors() {
    const had = this.hadShallowThisRep; this.hadShallowThisRep = false;
    return had ? { message: "Lift knees higher", speech: "Drive your knees up higher until your thighs are parallel to the floor." } : null;
  }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.leftHip >= 155 && a.rightHip >= 155;
  }
  getCalibrationChecks() {
    return [
      { id: "full_body_visible", message: "Step back so full body from shoulders to ankles is visible.",
        check: (lm) => maxVis(lm,"shoulder")>0.5 && maxVis(lm,"hip")>0.5 && maxVis(lm,"knee")>0.5 && maxVis(lm,"ankle")>0.5 },
      { id: "standing_upright", message: "Stand tall with both legs straight.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
