import { BicepCurlExercise } from "./BicepCurl.js";

export class BarbellCurlExercise extends BicepCurlExercise {
  static key = "barbell_curl";
  static displayName = "Barbell Curl";
  static startCue = "Arms fully straight, barbell in an underhand grip, elbows tucked.";
}