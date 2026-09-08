import { computeAngle, px, dist, maxVis, visibility } from "/js/landmarks.js";

export class CalfRaiseExercise {
  static key = "calf_raise";
  static displayName = "Calf Raise";
  static startCue = "Stand flat-footed with your knees straight.";
  static minRepDuration = 0.5;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["hip", "knee", "ankle", "heel", "foot_index"];
  static orientation = "portrait";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.baselineHeelLift = 0; this.reachedUpPhase = false; this.lastCountTime = 0;
    this.isCalibrated = false;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_heel")+visibility(lm,"left_foot_index"))/2;
    const rightVis = (visibility(lm,"right_heel")+visibility(lm,"right_foot_index"))/2;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const kneeAngle = computeAngle(lm, `${side}_hip`, `${side}_knee`, `${side}_ankle`, w, h);
    const heel = px(lm, `${side}_heel`, w, h), toe = px(lm, `${side}_foot_index`, w, h);
    const knee = px(lm, `${side}_knee`, w, h), ankle = px(lm, `${side}_ankle`, w, h);
    const shin = dist(knee, ankle) + 1e-6;
    return { kneeAngle, heelLift: (toe[1] - heel[1]) / shin, activeSide: side };
  }
  getFsmState(a) {
    if (this.isCalibrated && (this.currentState === null || this.currentState === "down"))
      this.baselineHeelLift = 0.85 * this.baselineHeelLift + 0.15 * a.heelLift;
    const delta = a.heelLift - this.baselineHeelLift;
    if (delta >= 0.18) { this.reachedUpPhase = true; return "up"; }
    if (delta <= 0.05) return "down";
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "down" && this.reachedUpPhase) { this.reachedUpPhase = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (a.kneeAngle < 155) errors.push({ message: "Keep knees straight", speech: "Keep your legs straight and drive up through your toes." });
    return errors;
  }
  getRepQualityErrors() { return null; }
  checkStartPosture(lm, w, h) { return this.computeAngles(lm, w, h).heelLift < 0.10; }
  getCalibrationChecks() {
    return [
      { id: "feet_visible", message: "Step back so your legs and feet are fully visible.",
        check: (lm) => maxVis(lm,"heel") > 0.4 && maxVis(lm,"foot_index") > 0.4 },
      { id: "flat_footed", message: "Stand upright and flat-footed with heels down.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}