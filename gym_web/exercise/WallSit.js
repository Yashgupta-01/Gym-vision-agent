import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class WallSitExercise {
  static key = "wall_sit";
  static displayName = "Wall Sit";
  static isDurationBased = true;
  static startCue = "Slide back against the wall and bend your knees to 90 degrees.";
  static minRepDuration = 5.0;
  static calibrationDuration = 2.5;
  static trackedLandmarks = ["shoulder", "hip", "knee", "ankle"];
  static orientation = "landscape";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.holdStartTime = 0; this.wasHolding = false; this.lastCountTime = 0;
    this._currentTime = 0;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_shoulder")+visibility(lm,"left_hip")+visibility(lm,"left_knee")+visibility(lm,"left_ankle"))/4;
    const rightVis = (visibility(lm,"right_shoulder")+visibility(lm,"right_hip")+visibility(lm,"right_knee")+visibility(lm,"right_ankle"))/4;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    return {
      knee: computeAngle(lm, `${side}_hip`, `${side}_knee`, `${side}_ankle`, w, h),
      hip: computeAngle(lm, `${side}_shoulder`, `${side}_hip`, `${side}_knee`, w, h),
    };
  }
  getFsmState(a) {
    if (a.knee >= 80 && a.knee <= 105 && a.hip >= 75 && a.hip <= 115) {
      if (!this.wasHolding) { this.holdStartTime = this._currentTime; this.wasHolding = true; }
      return "hold";
    }
    this.wasHolding = false;
    return "break";
  }
  shouldCount() {
    if (this.prevState === "hold" && this.currentState === "break")
      return (this._currentTime - this.holdStartTime) >= this.constructor.minRepDuration;
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (a.knee > 105) errors.push({ message: "Sink lower", speech: "Sink lower until your thighs are parallel to the floor." });
    else if (a.knee < 75) errors.push({ message: "Too low", speech: "Raise your hips slightly to bring knees to 90 degrees." });
    if (a.hip < 75) errors.push({ message: "Keep back flat", speech: "Keep your back flat against the wall and chest up." });
    return errors;
  }
  getRepQualityErrors() { return null; }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.knee >= 80 && a.knee <= 105 && a.hip >= 75 && a.hip <= 115;
  }
  getCalibrationChecks() {
    return [
      { id: "full_body_visible", message: "Stand against the wall in side view so shoulders, hips, knees, and feet are visible.",
        check: (lm) => maxVis(lm,"shoulder")>0.5 && maxVis(lm,"hip")>0.5 && maxVis(lm,"knee")>0.5 && maxVis(lm,"ankle")>0.5 },
      { id: "wall_sit_start", message: "Slide down into a wall sit with thighs parallel and hold.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
