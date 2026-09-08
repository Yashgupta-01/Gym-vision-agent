

import { BenchPressExercise } from "./BenchPress.js";
import { BentOverRowExercise } from "./BentOverRow.js";
import { BicepCurlExercise } from "./BicepCurl.js";
import { CalfRaiseExercise } from "./CalfRaise.js";
import { DeadLiftExercise } from "./DeadLift.js";
import { GluteBridgeExercise } from "./GluteBridge.js";
import { HammerCurlExercise } from "./HammerCurl.js";
import { JumpingJackExercise } from "./JumpingJack.js";
import { JumpingJackExercise } from "./JumpingJack.js";
import { LatPulldownExercise } from "./LatPullDown.js";
import { LatRaiseExercise } from "./LatRaise.js";
import { LegRaiseExercise } from "./LegRaise.js";
import { LungeExercise } from "./Lung.js";
import { LungExercise } from "./Lung.js";
import { OverheadTricepExtensionExercise } from "./OverheadTricepExtension.js";
import { PlankExercise } from "./Plank.js";
import { PushUpExercise } from "./PushUp.js";
import { RussianTwistExercise } from "./RussianTwist.js";
import { SitUpExercise } from "./SitUp.js";
import { SquatExercise } from "./Squat.js";
import { TricepsDipExercise } from "./TricepsDip.js";
import { WallSitExercise } from "./WallSit.js";

export const Exercises ={
  benchpress: BenchPressExercise,
  bentoverrow: BentOverRowExercise,
  bicepcurl: BicepCurlExercise,
  calfraise: CalfRaiseExercise,
  deadlift: DeadLiftExercise,
  glutebridge: GluteBridgeExercise,
  hammercurl: HammerCurlExercise,
  jumpingjack: JumpingJackExercise,
  latpulldown: LatPulldownExercise,
  latraise: LatRaiseExercise,
  legraise: LegRaiseExercise,
  lunge: LungeExercise,
  overheadtricepextension: OverheadTricepExtensionExercise,
  plank: PlankExercise,
  pushup: PushUpExercise,
  russiantwist: RussianTwistExercise,
  situp: SitUpExercise,
  squat: SquatExercise,
  tricepsdip: TricepsDipExercise,
  wallsit: WallSitExercise,
}

export function createExercise(key){
  const Cls = Exercises[key];
  if (!Cls) throw new Error("Unknown exercise: " + key);
  return new Cls();
}
