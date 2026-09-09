import { BentOverRowExercise } from "./BentOverRow.js";

export class SeatedCableRowExercise extends BentOverRowExercise {
  static key = "seated_cable_row";
  static displayName = "Seated Cable Row";
  static startCue = "Sit tall, arms extended forward holding the handle, slight lean.";
  // Seated: no forced hip-hinge start pose
  checkStartPosture(lm, w, h) {
    const a = this.computeAngles(lm, w, h);
    return a.armPull >= 150;
  }
  getCalibrationChecks() {
    return [
      { id: "upper_body_visible_side", message: "Set up in side view so your shoulder, elbow, and hip are visible.",
        check: (lm) => maxVis(lm, "shoulder") > 0.5 && maxVis(lm, "elbow") > 0.5 && maxVis(lm, "hip") > 0.5 },
      { id: "arms_extended_start", message: "Arms fully extended forward holding the handle.",
        check: (lm, w, h) => this.checkStartPosture(lm, w, h) },
    ];
  }
}