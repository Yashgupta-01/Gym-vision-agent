import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class BicepCurlExercise {
  static key = "bicep_curl";
  static displayName = "Bicep Curl";
  static startCue = "Tuck your elbows in. Start with your arms fully straight.";
  static minRepDuration = 0.7;
  static calibrationDuration = 2.0;
  static trackedLandmarks = ["shoulder", "elbow", "wrist", "hip"];
  static orientation = "portrait";

  constructor() { this.reset(); }
  reset() {
    this.currentState = null; this.prevState = null;
    this.reachedUp = false; this.hadDriftThisRep = false; this.lastCountTime = 0;
  }
  computeAngles(lm, w, h) {
    const leftElbow = computeAngle(lm, "left_shoulder", "left_elbow", "left_wrist", w, h);
    const rightElbow = computeAngle(lm, "right_shoulder", "right_elbow", "right_wrist", w, h);
    const curlingElbow = Math.min(leftElbow, rightElbow);
    const ls = px(lm,"left_shoulder",w,h), rs = px(lm,"right_shoulder",w,h);
    const le = px(lm,"left_elbow",w,h), re = px(lm,"right_elbow",w,h);
    const lh = px(lm,"left_hip",w,h), rh = px(lm,"right_hip",w,h);
    const scale = Math.max(dist(ls, rs), Math.max(dist(ls,lh), dist(rs,rh))) + 1e-6;
    return { leftElbow, rightElbow, curlingElbow, lDrift: Math.abs(le[0]-ls[0])/scale, rDrift: Math.abs(re[0]-rs[0])/scale };
  }
  getFsmState(a) {
    if (a.curlingElbow >= 145) return "down";
    if (a.curlingElbow <= 60) { this.reachedUp = true; return "up"; }
    return "mid";
  }
  shouldCount() {
    if (this.currentState === "down" && this.reachedUp) { this.reachedUp = false; return true; }
    return false;
  }
  checkFormErrors(a) {
    const errors = [];
    if (this.prevState === "down" && this.currentState !== "down") this.hadDriftThisRep = false;
    let activeDrift;
    if (a.leftElbow < 120 && a.rightElbow > 140) activeDrift = a.lDrift;
    else if (a.rightElbow < 120 && a.leftElbow > 140) activeDrift = a.rDrift;
    else activeDrift = Math.max(a.lDrift, a.rDrift);
    if (activeDrift > 0.30 && a.curlingElbow < 140) {
      this.hadDriftThisRep = true;
      errors.push({ message: "Elbows drifting", speech: "Keep your elbows pinned to your sides. Don't let them swing." });
    }
    return errors;
  }
  getRepQualityErrors() {
    const had = this.hadDriftThisRep; this.hadDriftThisRep = false;
    return had ? { message: "Elbows drifting", speech: "Keep your elbows pinned to your sides. Don't let them swing." } : null;
  }
  checkStartPosture(lm, w, h) { return this.computeAngles(lm, w, h).curlingElbow > 145; }
  getCalibrationChecks() {
    return [
      { id: "upper_body_visible", message: "Step back so your upper body and arms are fully visible.",
        check: (lm) => maxVis(lm,"shoulder") > 0.5 && maxVis(lm,"wrist") > 0.5 && maxVis(lm,"hip") > 0.5 },
      { id: "arms_straight", message: "Start with your arms fully straight, hanging down.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}
