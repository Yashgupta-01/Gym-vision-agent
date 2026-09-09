import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class MountainClimberExercise {
  static key = "mountain_climber";
  static displayName = "Mountain Climbers";
  static startCue = "Get into a straight-arm plank in side view.";
  static minRepDuration = 0.3;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "hip", "knee", "ankle"];
  static orientation = "landscape";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedKneeIn = false; this.lastCountTime = 0;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_shoulder")+visibility(lm,"left_hip")+visibility(lm,"left_knee")+visibility(lm,"left_ankle"))/4;
    const rightVis = (visibility(lm,"right_shoulder")+visibility(lm,"right_hip")+visibility(lm,"right_knee")+visibility(lm,"right_ankle"))/4;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const leftHip = computeAngle(lm, "left_shoulder", "left_hip", "left_knee", w, h);
    const rightHip = computeAngle(lm, "right_shoulder", "right_hip", "right_knee", w, h);
    const s = px(lm, `${side}_shoulder`, w, h), hip = px(lm, `${side}_hip`, w, h), a = px(lm, `${side}_ankle`, w, h);
    const torso = dist(s, hip) + 1e-6;
    let expectedY;
    if (Math.abs(a[0] - s[0]) > 1e-3) {
      const t = (hip[0] - s[0]) / (a[0] - s[0]);
      expectedY = s[1] + t * (a[1] - s[1]);
    } else expectedY = (s[1] + a[1]) / 2;
    return {
      leftHip, rightHip, activeHip: Math.min(leftHip, rightHip),
      normHipDev: (hip[1] - expectedY) / torso,
    };
  }
  getFsmState(a) {
    if (a.activeHip <= 95) { this.reachedKneeIn = true; return "knee_in"; }
    if (a.leftHip >= 145 && a.rightHip >= 145) return "extended";
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "extended" && this.reachedKneeIn) { this.reachedKneeIn = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (a.normHipDev < -0.15) errors.push({ message: "Keep hips down", speech: "Keep your hips in line with your shoulders and plank." });
    else if (a.activeHip > 95 && a.activeHip <= 120)
      errors.push({ message: "Drive knee closer", speech: "Drive your knee closer toward your chest." });
    return errors;
  }
  getRepQualityErrors() { return null; }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.leftHip >= 145 && a.rightHip >= 145 && Math.abs(a.normHipDev) <= 0.15;
  }
  getCalibrationChecks() {
    return [
      { id: "full_body_visible_side", message: "Set up in side view so shoulders, hips, knees, and ankles are visible.",
        check: (lm) => maxVis(lm,"shoulder")>0.5 && maxVis(lm,"hip")>0.5 && maxVis(lm,"ankle")>0.5 },
      { id: "straight_plank", message: "Hold a solid straight-arm plank to begin.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}