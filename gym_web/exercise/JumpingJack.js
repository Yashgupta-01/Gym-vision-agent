import { computeAngle, px, dist, maxVis, visibility } from "js/landmarks.js";

export class JumpingJackExercise {
  static key = "jumping_jack";
  static displayName = "Jumping Jacks";
  static startCue = "Stand tall facing the camera, arms down at sides, feet together.";
  static minRepDuration = 0.4;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["hip", "shoulder", "wrist", "ankle"];
  static orientation = "portrait";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedOpen = false; this.hadArmsLowThisRep = false; this.hadFeetNarrowThisRep = false; this.lastCountTime = 0;
  }
  computeAngles(lm, w, h) {
    const leftArm = computeAngle(lm, "left_hip", "left_shoulder", "left_wrist", w, h);
    const rightArm = computeAngle(lm, "right_hip", "right_shoulder", "right_wrist", w, h);
    const la = px(lm,"left_ankle",w,h), ra = px(lm,"right_ankle",w,h);
    const ls = px(lm,"left_shoulder",w,h), rs = px(lm,"right_shoulder",w,h);
    return { avgArm: (leftArm + rightArm) / 2, stanceRatio: dist(la, ra) / (dist(ls, rs) + 1e-6) };
  }
  getFsmState(a) {
    if (a.avgArm >= 130 && a.stanceRatio >= 1.2) { this.reachedOpen = true; return "open"; }
    if (a.avgArm <= 45 && a.stanceRatio <= 0.95) return "closed";
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "closed" && this.reachedOpen) { this.reachedOpen = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "closed" && this.currentState !== "closed") {
      this.hadArmsLowThisRep = false; this.hadFeetNarrowThisRep = false;
    }
    if (a.stanceRatio >= 1.2 && a.avgArm < 115) {
      this.hadArmsLowThisRep = true;
      errors.push({ message: "Raise arms higher", speech: "Raise your arms fully above your head." });
    } else if (a.avgArm >= 130 && a.stanceRatio < 1.05) {
      this.hadFeetNarrowThisRep = true;
      errors.push({ message: "Jump wider", speech: "Jump your feet out wider to at least shoulder width." });
    }
    return errors;
  }
  getRepQualityErrors() {
    const armsLow = this.hadArmsLowThisRep, feetNarrow = this.hadFeetNarrowThisRep;
    this.hadArmsLowThisRep = false; this.hadFeetNarrowThisRep = false;
    if (armsLow) return { message: "Raise arms higher", speech: "Raise your arms fully above your head." };
    if (feetNarrow) return { message: "Jump wider", speech: "Jump your feet out wider to at least shoulder width." };
    return null;
  }
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.avgArm <= 40 && a.stanceRatio <= 1.0;
  }
  getCalibrationChecks() {
    return [
      { id: "full_body_visible_frontal", message: "Face the camera so hands, feet, and whole body are visible.",
        check: (lm) => visibility(lm,"left_shoulder")>0.5 && visibility(lm,"right_shoulder")>0.5 &&
                       visibility(lm,"left_wrist")>0.5 && visibility(lm,"right_wrist")>0.5 &&
                       visibility(lm,"left_ankle")>0.5 && visibility(lm,"right_ankle")>0.5 },
      { id: "neutral_start", message: "Stand tall with feet together and arms down at your sides.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
