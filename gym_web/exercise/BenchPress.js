import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class BenchPressExercise {
  static key = "bench_press";
  static displayName = "Bench Press";
  static startCue = "Lie back with arms fully extended, bar or dumbbells locked out above your chest.";
  static minRepDuration = 1.0;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "elbow", "wrist", "hip"];
  static orientation = "landscape"; // side view, same as PushUp/Deadlift/TricepDip

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedDown = false; this.hadFlareThisRep = false; this.lastCountTime = 0;
  }
  _activeSide(lm) {
    const leftVis = (visibility(lm,"left_shoulder")+visibility(lm,"left_elbow")+visibility(lm,"left_wrist"))/3;
    const rightVis = (visibility(lm,"right_shoulder")+visibility(lm,"right_elbow")+visibility(lm,"right_wrist"))/3;
    return leftVis >= rightVis ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const elbow = computeAngle(lm, `${side}_shoulder`, `${side}_elbow`, `${side}_wrist`, w, h);
    // Elbow flare: angle between the torso line (hip->shoulder) and the
    // upper arm (shoulder->elbow). Small angle = elbows tucked; large
    // angle (~90+) = elbows flared straight out to the sides, a common
    // shoulder-strain cue.
    const flare = computeAngle(lm, `${side}_hip`, `${side}_shoulder`, `${side}_elbow`, w, h);
    // Bar-path drift: horizontal offset of the wrist from the shoulder,
    // normalized by upper-arm length — the bar/dumbbells should travel
    // in a roughly straight vertical line above the shoulder, not drift
    // toward the head or the waist.
    const s = px(lm, `${side}_shoulder`, w, h), wr = px(lm, `${side}_wrist`, w, h), e = px(lm, `${side}_elbow`, w, h);
    const upperArm = dist(s, e) + 1e-6;
    const barDrift = Math.abs(wr[0] - s[0]) / upperArm;
    return { elbow, flare, barDrift, activeSide: side };
  }
  getFsmState(a) {
    if (a.elbow >= 160) return "up";
    if (a.elbow <= 90) { this.reachedDown = true; return "down"; }
    return "mid";
  }
  shouldCount() {
    // Rep starts and ends at lockout ("up"), same debounced pattern as
    // every other exercise in the file.
    if (this.currentState === "up" && this.reachedDown) { this.reachedDown = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "up" && this.currentState !== "up") this.hadFlareThisRep = false;
    if (a.flare > 95 && a.elbow < 150) {
      this.hadFlareThisRep = true;
      errors.push({ message: "Elbows flaring", speech: "Tuck your elbows in slightly, don't flare them straight out to the sides." });
    } else if (a.barDrift > 0.5 && a.elbow < 150) {
      errors.push({ message: "Control the bar path", speech: "Keep the bar moving in a straight line above your chest." });
    }
    return errors;
  }
  getRepQualityErrors() {
    const had = this.hadFlareThisRep; this.hadFlareThisRep = false;
    return had ? { message: "Elbows flaring", speech: "Tuck your elbows in slightly, don't flare them straight out to the sides." } : null;
  }
  checkStartPosture(lm, w, h) { return this.computeAngles(lm, w, h).elbow >= 150; }
  getCalibrationChecks() {
    return [
      { id: "upper_body_visible_side", message: "Set up in side view so your shoulder, elbow, and wrist are visible.",
        check: (lm) => maxVis(lm,"shoulder")>0.5 && maxVis(lm,"elbow")>0.5 && maxVis(lm,"wrist")>0.5 },
      { id: "arms_locked_out", message: "Start with the bar or dumbbells locked out above your chest, arms straight.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
