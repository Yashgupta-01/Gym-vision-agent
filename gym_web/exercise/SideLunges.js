import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class SideLungeExercise {
  static key = "side_lunge";
  static displayName = "Side Lunge";
  static startCue = "Stand facing the camera with feet wide and both legs straight.";
  static minRepDuration = 0.8;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["hip", "knee", "ankle", "shoulder"];
  static orientation = "portrait";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedDown = false; this.lastCountTime = 0;
  }
  computeAngles(lm, w, h) {
    const leftKnee = computeAngle(lm, "left_hip", "left_knee", "left_ankle", w, h);
    const rightKnee = computeAngle(lm, "right_hip", "right_knee", "right_ankle", w, h);
    const la = px(lm,"left_ankle",w,h), ra = px(lm,"right_ankle",w,h);
    const ls = px(lm,"left_shoulder",w,h), rs = px(lm,"right_shoulder",w,h);
    return {
      leftKnee, rightKnee,
      workingKnee: Math.min(leftKnee, rightKnee),
      straightKnee: Math.max(leftKnee, rightKnee),
      stanceRatio: dist(la, ra) / (dist(ls, rs) + 1e-6),
    };
  }
  getFsmState(a) {
    if (a.workingKnee >= 155) return "up";
    if (a.workingKnee <= 100) { this.reachedDown = true; return "down"; }
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "up" && this.reachedDown) { this.reachedDown = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (a.workingKnee < 125 && a.straightKnee < 155)
      errors.push({ message: "Keep one leg straight", speech: "Keep your non-lunging leg completely straight as you sit back." });
    if (a.workingKnee > 100 && a.workingKnee <= 125 && this.prevState === "mid")
      errors.push({ message: "Lunge deeper", speech: "Sink lower until your thigh is parallel to the floor." });
    if (a.workingKnee < 140 && a.stanceRatio < 1.3)
      errors.push({ message: "Widen your stance", speech: "Take a wider step out to the side before lunging." });
    return errors;
  }
  getRepQualityErrors() { return null; }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.leftKnee >= 155 && a.rightKnee >= 155;
  }
  getCalibrationChecks() {
    return [
      { id: "full_body_visible_frontal", message: "Face the camera so full body from shoulders to ankles is visible.",
        check: (lm) => maxVis(lm,"shoulder")>0.5 && maxVis(lm,"hip")>0.5 && maxVis(lm,"knee")>0.5 && maxVis(lm,"ankle")>0.5 },
      { id: "standing_upright", message: "Stand tall facing forward with both legs straight.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
