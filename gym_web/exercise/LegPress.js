// gym_web/exercise/LegPress.js
import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class LegPressExercise {
  static key = "leg_press";
  static displayName = "Leg Press";
  static startCue = "Seated on the machine, knees bent toward your chest, feet on the platform.";
  static minRepDuration = 0.9;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["hip", "knee", "ankle"];
  static orientation = "landscape";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedDown = false; this.hadIncompleteLockThisRep = false; this.lastCountTime = 0;
  }
  _activeSide(lm) {
    const l = (visibility(lm,"left_hip")+visibility(lm,"left_knee")+visibility(lm,"left_ankle"))/3;
    const r = (visibility(lm,"right_hip")+visibility(lm,"right_knee")+visibility(lm,"right_ankle"))/3;
    return l >= r ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const knee = computeAngle(lm, `${side}_hip`, `${side}_knee`, `${side}_ankle`, w, h);
    return { knee, activeSide: side };
  }
  getFsmState(a) {
    if (a.knee <= 100) { this.reachedDown = true; return "down"; }
    if (a.knee >= 165) return "up";
    return "mid";
  }
  shouldCount() {
    // Rep starts/ends at lockout ("up"), same convention as Squat/PushUp —
    // counts on return to lockout after visiting the bottom.
    if (this.currentState === "up" && this.reachedDown) { this.reachedDown = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "up" && this.currentState !== "up") this.hadIncompleteLockThisRep = false;
    // Locking knees out hard past near-full extension without control is a
    // common injury risk on this machine — flag going fully rigid/hyperextending
    // isn't measurable from 2D angle alone, so this stays a depth check only:
    // catches a rep that never got below a real working depth.
    if (a.knee > 100 && a.knee <= 130 && this.currentState === "mid" && this.prevState === "down") {
      this.hadIncompleteLockThisRep = true;
      errors.push({ message: "Press fully", speech: "Extend your legs fully at the top, don't cut the press short." });
    }
    return errors;
  }
  getRepQualityErrors() {
    const had = this.hadIncompleteLockThisRep; this.hadIncompleteLockThisRep = false;
    return had ? { message: "Press fully", speech: "Extend your legs fully at the top, don't cut the press short." } : null;
  }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.knee >= 80 && a.knee <= 110;
  }
  getCalibrationChecks() {
    return [
      { id: "legs_visible_side", message: "Side view — hips, knees, and ankles must be visible.",
        check: (lm) => maxVis(lm,"hip")>0.5 && maxVis(lm,"knee")>0.5 && maxVis(lm,"ankle")>0.5 },
      { id: "knees_bent_start", message: "Start with your knees bent toward your chest, ready to press.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
