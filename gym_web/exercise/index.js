import { BarbellBackSquatExercise } from "./BarbellBackSquat.js";
import { BarbellCalfRaiseExercise } from "./BarbellCalfRaise.js";
import { BarbellCurlExercise } from "./BarbellCurl.js";
import { BarbellOverheadPressExercise } from "./BarbellOverheadPress.js";
import { BenchDipExercise } from "./BenchDip.js";
import { BenchPressExercise } from "./BenchPress.js";
import { BentOverRowExercise } from "./BentOverRow.js";
import { BicepCurlExercise } from "./BicepCurl.js";
import { CableCalfRaiseExercise } from "./CableCalfRaise.js";
import { CableChestFlyExercise } from "./CableChestFly.js";
import { CableCurlExercise } from "./CableCurl.js";
import { CableLateralRaiseExercise } from "./CableLateralRaise.js";
import { CalfRaiseExercise } from "./CalfRaises.js";
import { ChestPressMachineExercise } from "./ChestPressMachine.js";
import { DeadliftExercise } from "./Deadlift.js";
import { DiamondPushUpExercise } from "./DiamondPushup.js";
import { EzBarCurlExercise } from "./EzBarCurl.js";
import { FlyExercise } from "./Fly.js";
import { FrontRaiseExercise } from "./FrontRaise.js";
import { GluteBridgeExercise } from "./GluteBridge.js";
import { HackSquatExercise } from "./HackSquat.js";
import { HammerCurlExercise } from "./HammerCurl.js";
import { HighKneesExercise } from "./HighKnees.js";
import { InclineBenchPressExercise } from "./InclineBenchPress.js";
import { InclinePushUpExercise } from "./InclinePushup.js";
import { JumpingJackExercise } from "./JumpingJack.js";
import { LateralRaiseExercise } from "./LateralRaise.js";
import { LatPulldownExercise } from "./LatPullDown.js";
import { LegCurlExercise } from "./LegCurl.js";
import { LegPressExercise } from "./LegPress.js";
import { LegRaiseExercise } from "./LegRaise.js";
import { LungeExercise } from "./Lunges.js";
import { MachineShoulderPressExercise } from "./MachineShoulderPress.js";
import { MountainClimberExercise } from "./MountainClimber.js";
import { OverheadTricepExtensionExercise } from "./OverheadTricepExtension.js";
import { PecDeckExercise } from "./PecDeck.js";
import { PlankExercise } from "./Plank.js";
import { PreacherCurlExercise } from "./PreacherCurl.js";
import { PushUpExercise } from "./Pushup.js";
import { RearDeltFlyExercise } from "./RearDeltFly.js";
import { RussianTwistExercise } from "./RussianTwist.js";
import { SeatedCableRowExercise } from "./SeatedCableRow.js";
import { ShoulderPressExercise } from "./ShoulderPress.js";
import { SideLungeExercise } from "./SideLunges.js";
import { SitUpExercise } from "./SitUp.js";
import { SquatExercise } from "./Squat.js";
import { TricepDipExercise } from "./TricepDip.js";
import { TricepKickbackExercise } from "./TricepKickback.js";
import { WallSitExercise } from "./WallSit.js";





export const Exercises = {
  barbell_back_squat: BarbellBackSquatExercise,
  barbell_calf_raise: BarbellCalfRaiseExercise,
  barbell_curl: BarbellCurlExercise,
  barbell_overhead_press: BarbellOverheadPressExercise,
  bench_dip: BenchDipExercise,
  bench_press: BenchPressExercise,
  bent_over_row: BentOverRowExercise,
  bicep_curl: BicepCurlExercise,
  cable_calf_raise: CableCalfRaiseExercise,
  cable_chest_fly: CableChestFlyExercise,
  cable_curl: CableCurlExercise,
  cable_lateral_raise: CableLateralRaiseExercise,
  calf_raise: CalfRaiseExercise,
  chest_press_machine: ChestPressMachineExercise,
  deadlift: DeadliftExercise,
  diamond_push_up: DiamondPushupExercise,
  ez_bar_curl: EzBarCurlExercise,
  fly: FlyExercise,
  front_raise: FrontRaiseExercise,
  glute_bridge: GluteBridgeExercise,
  hack_squat: HackSquatExercise,
  hammer_curl: HammerCurlExercise,
  high_knees: HighKneesExercise,
  incline_bench_press: InclineBenchPressExercise,
  incline_push_up: InclinePushupExercise,
  jumping_jack: JumpingJackExercise,
  lat_pulldown: LatPulldownExercise,
  lateral_raise: LateralRaiseExercise,
  leg_curl: LegCurlExercise,
  leg_press: LegPressExercise,
  leg_raise: LegRaiseExercise,
  lunge: LungeExercise,
  machine_shoulder_press: MachineShoulderPressExercise,
  mountain_climber: MountainClimberExercise,
  overhead_tricep_extension: OverheadTricepExtensionExercise,
  pec_deck: PecDeckExercise,
  plank: PlankExercise,
  preacher_curl: PreacherCurlExercise,
  push_up: PushUpExercise,
  rear_delt_fly: RearDeltFlyExercise,
  russian_twist: RussianTwistExercise,
  seated_cable_row: SeatedCableRowExercise,
  shoulder_press: ShoulderPressExercise,
  side_lunge: SideLungeExercise,
  sit_up: SitUpExercise,
  squat: SquatExercise,
  tricep_dip: TricepDipExercise,
  tricep_kickback: TricepKickbackExercise,
  wall_sit: WallSitExercise,
}


export function createExercise(key) {
  const Cls = Exercises[key];
  if (!Cls) throw new Error("Unknown exercise: " + key);
  return new Cls();
};