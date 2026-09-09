import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class GluteBridgeExercise {
  static key = "glute_bridge";
  static displayName = "Glute Bridge";
  static startCue = "Lie flat on your back with knees bent and feet flat on the floor.";
  static minRepDuration = 0.8;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "hip", "knee", "ankle"];
  static orientation = null;

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedUp = false; this.hadFeetPlacementThisRep = false; this.feetReason = null; this.lastCountTime = 0;
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
    if (a.hip >= 155) { this.reachedUp = true; return "up"; }
    if (a.hip <= 105) return "down";
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "down" && this.reachedUp) { this.reachedUp = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "down" && this.currentState !== "down") {
      this.hadFeetPlacementThisRep = false; this.feetReason = null;
    }
    if (a.knee > 125) {
      this.hadFeetPlacementThisRep = true;
      this.feetReason = { message: "Bring feet closer", speech: "Walk your feet closer to your glutes." };
      errors.push(this.feetReason);
    } else if (a.knee < 65) {
      this.hadFeetPlacementThisRep = true;
      this.feetReason = { message: "Move feet forward", speech: "Move your feet slightly further away from your glutes." };
      errors.push(this.feetReason);
    }
    if (a.hip > 115 && a.hip < 145 && this.prevState === "mid")
      errors.push({ message: "Squeeze glutes higher", speech: "Squeeze your glutes and drive your hips all the way up." });
    return errors;
  }
  getRepQualityErrors() {
    const had = this.hadFeetPlacementThisRep; const reason = this.feetReason;
    this.hadFeetPlacementThisRep = false; this.feetReason = null;
    return had ? reason : null;
  }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.hip <= 105 && a.knee >= 70 && a.knee <= 120;
  }
  getCalibrationChecks() {
    return [
      { id: "full_body_visible_side", message: "Lie down in side view so shoulders, hips, knees, and ankles are clear.",
        check: (lm) => maxVis(lm,"shoulder")>0.5 && maxVis(lm,"hip")>0.5 && maxVis(lm,"knee")>0.5 && maxVis(lm,"ankle")>0.5 },
      { id: "resting_start", message: "Lie flat with knees bent and hips down.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}