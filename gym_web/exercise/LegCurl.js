// gym_web/exercise/LegCurl.js
import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class LegCurlExercise {
  static key = "leg_curl";
  static displayName = "Leg Curl";
  static startCue = "Lie face down (or seated) on the machine, legs extended straight, pad against your ankles.";
  static minRepDuration = 0.8;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["hip", "knee", "ankle"];
  static orientation = "landscape";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedUp = false; this.hadHipLiftThisRep = false; this.lastCountTime = 0;
    this.baselineHipAngle = null;
  }
  _activeSide(lm) {
    const l = (visibility(lm,"left_hip")+visibility(lm,"left_knee")+visibility(lm,"left_ankle"))/3;
    const r = (visibility(lm,"right_hip")+visibility(lm,"right_knee")+visibility(lm,"right_ankle"))/3;
    return l >= r ? "left" : "right";
  }
  computeAngles(lm, w, h) {
    const side = this._activeSide(lm);
    const knee = computeAngle(lm, `${side}_hip`, `${side}_knee`, `${side}_ankle`, w, h);
    // Hip stability: shoulder isn't tracked reliably face-down, so use knee-
    // to-hip line stability via hip's own y-position drift isn't available
    // without shoulder either — approximate cheat detection via hip angle
    // relative to a captured baseline is skipped for this exercise (unlike
    // BentOverRow/RearDeltFly) since a reliable third point isn't in frame
    // on most machine setups. Left as a documented limitation, not faked.
    return { knee, activeSide: side };
  }
  getFsmState(a) {
    if (a.knee >= 155) return "down";
    if (a.knee <= 60) { this.reachedUp = true; return "up"; }
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "down" && this.reachedUp) { this.reachedUp = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (a.knee > 60 && a.knee <= 90 && this.currentState === "mid" && this.prevState === "up")
      errors.push({ message: "Curl higher", speech: "Curl your heels closer to your glutes at the top." });
    return errors;
  }
  getRepQualityErrors() { return null; }
  checkStartPosture(lm, w, h) { return this.computeAngles(lm, w, h).knee >= 150; }
  getCalibrationChecks() {
    return [
      { id: "legs_visible_side", message: "Side view — hips, knees, and ankles must be visible.",
        check: (lm) => maxVis(lm,"hip")>0.5 && maxVis(lm,"knee")>0.5 && maxVis(lm,"ankle")>0.5 },
      { id: "legs_extended_start", message: "Start with your legs fully extended straight.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
