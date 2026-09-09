import { computeAngle, px, dist, maxVis, visibility } from "../js/landmarks.js";

export class SquatExercise {
    static key = "squat";
    static displayName = "Squat";
    static startCue = "Stand tall with your feet shoulder-width apart.";
    static minRepDuration = 1.0;
    static calibrationDuration = 1.5;
    static trackedLandmarks = ["hip", "knee", "ankle"];
    static orientation = "portrait";

    constructor() { this.reset(); }
    reset() {
        this.currentState = null; this.prevState = null;
        this.reachedDown = false; this.hadValgusThisRep = false; this.lastCountTime = 0;
    }
    computeAngles(lm, w, h) {
        const leftKnee = computeAngle(lm, "left_hip", "left_knee", "left_ankle", w, h);
        const rightKnee = computeAngle(lm, "right_hip", "right_knee", "right_ankle", w, h);
        const avgKnee = (leftKnee + rightKnee) / 2;
        const lk = px(lm, "left_knee", w, h), rk = px(lm, "right_knee", w, h);
        const la = px(lm, "left_ankle", w, h), ra = px(lm, "right_ankle", w, h);
        return { avgKnee, valgusRatio: dist(lk, rk) / (dist(la, ra) + 1e-6) };
    }
    getFsmState(a) {
        if (a.avgKnee >= 150) return "up";
        if (a.avgKnee <= 120) { this.reachedDown = true; return "down"; }
        return "mid";
    }
    shouldCount() {
        if (this.currentState === "up" && this.reachedDown) { this.reachedDown = false; return true; }
        return false;
    }
    checkFormErrors(a) {
        const errors = [];
        if (this.prevState === "up" && this.currentState !== "up") this.hadValgusThisRep = false;
        if (a.valgusRatio < 0.70 && a.avgKnee < 140) {
            this.hadValgusThisRep = true;
            errors.push({ message: "Knees caving in", speech: "Push your knees outward." });
        }
        return errors;
    }
    getRepQualityErrors() {
        const had = this.hadValgusThisRep; this.hadValgusThisRep = false;
        return had ? { message: "Knees caving in", speech: "Push your knees outward." } : null;
    }
    checkStartPosture(lm, w, h) { return this.computeAngles(lm, w, h).avgKnee >= 145; }
    getCalibrationChecks() {
        return [
            {
                id: "full_body_visible_frontal", message: "Face the camera and step back so your full body is visible.",
                check: (lm) => maxVis(lm, "ankle") > 0.3 && maxVis(lm, "shoulder") > 0.3
            },
            {
                id: "legs_straight", message: "Stand tall with your legs fully straight.",
                check: (lm, w, h) => this.checkStartPosture(lm, w, h)
            },
        ];
    }
}