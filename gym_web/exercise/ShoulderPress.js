import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class ShoulderPressExercise {
  static key = "shoulder_press";
  static displayName = "Shoulder Press";
  static startCue = "Hold your weights at shoulder height with your elbows bent.";
  static minRepDuration = 1.0;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "elbow", "wrist"];
  static orientation = "portrait";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedUp = false; this.hadUnevenPressThisRep = false; this.lastCountTime = 0;
  }
  computeAngles(lm, w, h) {
    const leftElbow = computeAngle(lm, "left_shoulder", "left_elbow", "left_wrist", w, h);
    const rightElbow = computeAngle(lm, "right_shoulder", "right_elbow", "right_wrist", w, h);
    const avgElbow = (leftElbow + rightElbow) / 2;
    const ls = px(lm,"left_shoulder",w,h), rs = px(lm,"right_shoulder",w,h);
    const lw = px(lm,"left_wrist",w,h), rw = px(lm,"right_wrist",w,h);
    return {
      leftElbow, rightElbow, avgElbow,
      elbowDiff: Math.abs(leftElbow - rightElbow),
      wristAboveShoulder: (lw[1] < ls[1]) && (rw[1] < rs[1]),
    };
  }
  getFsmState(a) {
    if (a.avgElbow >= 150 && a.wristAboveShoulder) { this.reachedUp = true; return "up"; }
    if (a.avgElbow <= 100) return "down";
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "down" && this.reachedUp) { this.reachedUp = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (a.elbowDiff > 25 && a.avgElbow > 100 && a.avgElbow < 150){
      this.hadUnevenPressThisRep = true;
      errors.push({ message: "Press evenly", speech: "Push up evenly with both arms. Keep your movement balanced." });
    }
    if (a.avgElbow >= 125 && a.avgElbow < 150 && this.currentState === "mid" && this.prevState === "up")
      errors.push({ message: "Full lockout", speech: "Fully extend your arms overhead at the top." });
    return errors;
  }
  getRepQualityErrors() {
      const had = this.hadUnevenPressThisRep; this.hadUnevenPressThisRep = false;
      return had ? { message: "Press evenly", speech: "Push up evenly with both arms. Keep your movement balanced." } : null;
  }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.avgElbow >= 75 && a.avgElbow <= 110;
  }
  getCalibrationChecks() {
    return [
      { id: "upper_body_visible_frontal", message: "Face the camera so your upper body and arms are fully visible.",
        check: (lm) => visibility(lm,"left_shoulder")>0.5 && visibility(lm,"right_shoulder")>0.5 &&
                       visibility(lm,"left_wrist")>0.5 && visibility(lm,"right_wrist")>0.5 },
      { id: "weights_at_shoulders", message: "Hold weights at shoulder height with elbows bent ~90°.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}