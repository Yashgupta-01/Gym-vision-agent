// js/landmarks.js
export const LM = {
  nose: 0,
  left_ear: 7, right_ear: 8,
  left_shoulder: 11, right_shoulder: 12,
  left_elbow: 13, right_elbow: 14,
  left_wrist: 15, right_wrist: 16,
  left_hip: 23, right_hip: 24,
  left_knee: 25, right_knee: 26,
  left_ankle: 27, right_ankle: 28,
  left_heel: 29, right_heel: 30,
  left_foot_index: 31, right_foot_index: 32,
};

export function px(landmarks, name, w, h) {
  const idx = LM[name];
  const l = landmarks[idx];
  if (!l) return [0, 0];
  return [l.x * w, l.y * h];
}

export function visibility(landmarks, name) {
  const idx = LM[name];
  const l = landmarks[idx];
  if (!l) return 0;
  return l.visibility ?? 1.0;
}

function angleBetween(a, b, c) {
  const ba = [a[0] - b[0], a[1] - b[1]];
  const bc = [c[0] - b[0], c[1] - b[1]];
  const dot = ba[0] * bc[0] + ba[1] * bc[1];
  const magBa = Math.hypot(ba[0], ba[1]);
  const magBc = Math.hypot(bc[0], bc[1]);
  const cos = Math.min(1, Math.max(-1, dot / (magBa * magBc + 1e-6)));
  return Math.acos(cos) * (180 / Math.PI);
}

export function computeAngle(landmarks, p1, p2, p3, w, h) {
  return angleBetween(px(landmarks, p1, w, h), px(landmarks, p2, w, h), px(landmarks, p3, w, h));
}

export function dist(a, b) {
  return Math.hypot(a[0] - b[0], a[1] - b[1]);
}

export function maxVis(lm, name) {
  return Math.max(visibility(lm, "left_" + name), visibility(lm, "right_" + name));
}