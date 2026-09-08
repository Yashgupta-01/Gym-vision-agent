// ─────────────────────────────────────────────────────────────
//  LAT PULLDOWN
//  Structurally the inverse of ShoulderPress: starts with arms
//  extended overhead ("up"), pulls down to the chest ("down"), counts
//  on return to "up" — same start/end naming convention as Squat/
//  PushUp/BenchPress. Adds a lean-back cheat check reusing the
//  hip-deviation pattern from PushUp/Plank.
// ─────────────────────────────────────────────────────────────

import { computeAngle, px, dist, maxVis, visibility } from "js/landmarks.js";


export
class LatPulldownExercise {
  static key = "lat_pulldown";
  static displayName = "Lat Pulldown";
  static startCue = "Reach up and grab the bar with arms fully extended overhead.";
  static minRepDuration = 0.8;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "elbow", "wrist", "hip"];
  static orientation = "portrait";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedDown = false; this.hadLeanThisRep = false; this.lastCountTime = 0;
  }
  computeAngles(lm, w, h) {
    const leftElbow = computeAngle(lm, "left_shoulder", "left_elbow", "left_wrist", w, h);
    const rightElbow = computeAngle(lm, "right_shoulder", "right_elbow", "right_wrist", w, h);
    const avgElbow = (leftElbow + rightElbow) / 2;
    const ls = px(lm,"left_shoulder",w,h), rs = px(lm,"right_shoulder",w,h);
    const lw = px(lm,"left_wrist",w,h), rw = px(lm,"right_wrist",w,h);
    const lh = px(lm,"left_hip",w,h);
    const wristBelowShoulder = (lw[1] > ls[1]) && (rw[1] > rs[1]);
    // Lean-back cheat check: horizontal offset of the shoulder midpoint
    // from the hip midline, normalized by torso length — catches
    // swinging the torso back to help the pull instead of using the lats.
    const shoulderMidX = (ls[0]+rs[0])/2;
    const torsoLen = dist(ls, lh) + 1e-6;
    const leanOffset = Math.abs(shoulderMidX - lh[0]) / torsoLen;
    return { avgElbow, wristBelowShoulder, leanOffset };
  }
  getFsmState(a) {
    if (a.avgElbow >= 150 && !a.wristBelowShoulder) return "up";
    if (a.avgElbow <= 90 && a.wristBelowShoulder) { this.reachedDown = true; return "down"; }
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "up" && this.reachedDown) { this.reachedDown = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "up" && this.currentState !== "up") this.hadLeanThisRep = false;
    if (a.leanOffset > 0.35) {
      this.hadLeanThisRep = true;
      errors.push({ message: "Leaning back", speech: "Keep your torso upright, don't lean back to swing the bar down." });
    } else if (a.avgElbow > 90 && a.avgElbow <= 115 && this.prevState === "mid") {
      errors.push({ message: "Pull lower", speech: "Pull the bar all the way down to your chest." });
    }
    return errors;
  }
  getRepQualityErrors() {
    const had = this.hadLeanThisRep; this.hadLeanThisRep = false;
    return had ? { message: "Leaning back", speech: "Keep your torso upright, don't lean back to swing the bar down." } : null;
  }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.avgElbow >= 150 && !a.wristBelowShoulder;
  }
  getCalibrationChecks() {
    return [
      { id: "upper_body_visible_frontal", message: "Face the camera so your shoulders, elbows, and wrists are visible.",
        check: (lm) => visibility(lm,"left_shoulder")>0.5 && visibility(lm,"right_shoulder")>0.5 &&
                       visibility(lm,"left_wrist")>0.5 && visibility(lm,"right_wrist")>0.5 },
      { id: "arms_overhead_start", message: "Reach up and grab the bar with your arms fully extended overhead.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}