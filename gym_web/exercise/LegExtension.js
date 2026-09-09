import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class LegExtensionExercise {
  static key = "leg_extension";
  static displayName = "Leg Extension";
  static startCue = "Sit on the machine, back against the pad, knees bent ~90°.";
  static minRepDuration = 0.8;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["hip", "knee", "ankle"];
  static orientation = "landscape";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedUp = false; this.hadIncompleteLockThisRep = false; this.lastCountTime = 0;
  }

  _activeSide(lm) {
    const l = (visibility(lm, "left_hip") + visibility(lm, "left_knee") + visibility(lm, "left_ankle")) / 3;
    const r = (visibility(lm, "right_hip") + visibility(lm, "right_knee") + visibility(lm, "right_ankle")) / 3;
    return l >= r ? "left" : "right";
  }

  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const knee = computeAngle(lm, `${side}_hip`, `${side}_knee`, `${side}_ankle`, w, h);
    return { knee, activeSide: side };
  }

  getFsmState(a) {
    // seated: down = knees bent (~90°), up = legs almost straight
    if (a.knee >= 155) { this.reachedUp = true; return "up"; }
    if (a.knee <= 105) return "down";
    return "mid";
  }

  shouldCount() {
    if (this.currentState === "down" && this.reachedUp) {
      this.reachedUp = false;
      return true;
    }
    return false;
  }

  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "down" && this.currentState !== "down") {
      this.hadIncompleteLockThisRep = false;
    }
    // rushed lockout / incomplete extension
    if (a.knee >= 130 && a.knee < 155 && this.currentState === "mid" && this.prevState === "up") {
      this.hadIncompleteLockThisRep = true;
      errors.push({
        message: "Full extension",
        speech: "Fully straighten your legs at the top. Don't cut the rep short.",
      });
    }
    return errors;
  }

  getRepQualityErrors() {
    const had = this.hadIncompleteLockThisRep;
    this.hadIncompleteLockThisRep = false;
    return had
      ? { message: "Full extension", speech: "Fully straighten your legs at the top. Don't cut the rep short." }
      : null;
  }

  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.knee >= 85 && a.knee <= 115;
  }

  getCalibrationChecks() {
    return [
      {
        id: "legs_visible_side",
        message: "Side view — hips, knees and ankles must be clear.",
        check: (lm) => maxVis(lm, "hip") > 0.5 && maxVis(lm, "knee") > 0.5 && maxVis(lm, "ankle") > 0.5,
      },
      {
        id: "seated_start",
        message: "Sit with knees bent about 90 degrees, pad against your shins.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h),
      },
    ];
  }
}
