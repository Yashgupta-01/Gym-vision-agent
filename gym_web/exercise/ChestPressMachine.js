import { BenchPressExercise } from "./BenchPress.js";

export class ChestPressMachineExercise extends BenchPressExercise {
  static key = "chest_press_machine";
  static displayName = "Chest Press Machine";
  static startCue = "Sit on the machine with handles at chest height, arms extended.";
  static orientation = "landscape";
}