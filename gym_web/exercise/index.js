import { BenchPressExercise } from "./BenchPress.js";
import { BentOverRowExercise } from "./BentOverRow.js";
import { BicepCurlExercise } from "./BicepCurl.js";
import { CalfRaiseExercise } from "./CalfRaises.js";
import { DeadliftExercise } from "./Deadlift.js";
import { FlyExercise } from "./Fly.js";
import { FrontRaiseExercise } from "./FrontRaise.js";
import { GluteBridgeExercise } from "./GluteBridge.js";
import { HammerCurlExercise } from "./HammerCurl.js";
import { HighKneesExercise } from "./HighKnees.js";
import { JumpingJackExercise } from "./JumpingJack.js";
import { LatPulldownExercise } from "./LatPullDown.js";
import { LateralRaiseExercise } from "./LateralRaise.js";
import { LegRaiseExercise } from "./LegRaise.js";
import { LungeExercise } from "./Lunges.js";
import { MountainClimberExercise } from "./MountainClimber.js";
import { OverheadTricepExtensionExercise } from "./OverheadTricepExtension.js";
import { PlankExercise } from "./Plank.js";
import { PushUpExercise } from "./Pushup.js";
import { RearDeltFlyExercise } from "./RearDeltFly.js";
import { RussianTwistExercise } from "./RussianTwist.js";
import { ShoulderPressExercise } from "./ShoulderPress.js";
import { SideLungeExercise } from "./SideLunges.js";
import { SitUpExercise } from "./SitUp.js";
import { SquatExercise } from "./Squat.js";
import { TricepDipExercise } from "./TricepDip.js";
import { TricepKickbackExercise } from "./TricepKickback.js";
import { WallSitExercise } from "./WallSit.js";
import { InclineBenchPressExercise } from "./InclineBenchPress.js";
import { ChestPressMachineExercise } from "./ChestPressMachine.js";
import { InclinePushUpExercise } from "./InclinePushup.js";
import { DiamondPushUpExercise } from "./DiamondPushup.js";
import { PecDeckExercise } from "./PecDeck.js";
import { CableChestFlyExercise } from "./CableChestFly.js";
import { BarbellOverheadPressExercise } from "./BarbellOverheadPress.js";
import { MachineShoulderPressExercise } from "./MachineShoulderPress.js";
import { CableLateralRaiseExercise } from "./CableLateralRaise.js";
import { BarbellCurlExercise } from "./BarbellCurl.js";
import { EzBarCurlExercise } from "./EzBarCurl.js";
import { CableCurlExercise } from "./CableCurl.js";
import { SeatedCableRowExercise } from "./SeatedCableRow.js";
import { HackSquatExercise } from "./HackSquat.js";
import { BarbellBackSquatExercise } from "./BarbellBackSquat.js";
import { BarbellCalfRaiseExercise } from "./BarbellCalfRaise.js";
import { CableCalfRaiseExercise } from "./CableCalfRaise.js";
import { BenchDipExercise } from "./BenchDip.js";



export const Exercises = {
  bench_press: BenchPressExercise,
  bent_over_row: BentOverRowExercise,
  bicep_curl: BicepCurlExercise,
  calf_raise: CalfRaiseExercise,
  deadlift: DeadliftExercise,
  fly: FlyExercise,
  front_raise: FrontRaiseExercise,
  glute_bridge: GluteBridgeExercise,
  hammer_curl: HammerCurlExercise,
  high_knees: HighKneesExercise,
  jumping_jack: JumpingJackExercise,
  lat_pulldown: LatPulldownExercise,
  lateral_raise: LateralRaiseExercise,
  leg_raise: LegRaiseExercise,
  lunge: LungeExercise,
  mountain_climber: MountainClimberExercise,
  overhead_tricep_extension: OverheadTricepExtensionExercise,
  plank: PlankExercise,
  push_up: PushUpExercise,
  rear_delt_fly: RearDeltFlyExercise,
  russian_twist: RussianTwistExercise,
  shoulder_press: ShoulderPressExercise,
  side_lunge: SideLungeExercise,
  sit_up: SitUpExercise,
  squat: SquatExercise,
  tricep_dip: TricepDipExercise,
  tricep_kickback: TricepKickbackExercise,
  wall_sit: WallSitExercise,
  incline_bench_press: InclineBenchPressExercise,
  chest_press_machine: ChestPressMachineExercise,
  incline_push_up: InclinePushupExercise,
  diamond_push_up: DiamondPushupExercise,
  pec_deck: PecDeckExercise,
  cable_chest_fly: CableChestFlyExercise,
  barbell_overhead_press: BarbellOverheadPressExercise,
  machine_shoulder_press: MachineShoulderPressExercise,
  cable_lateral_raise: CableLateralRaiseExercise,
  barbell_curl: BarbellCurlExercise,
  ez_bar_curl: EzBarCurlExercise,
  cable_curl: CableCurlExercise,
  seated_cable_row: SeatedCableRowExercise,
  hack_squat: HackSquatExercise,
  barbell_back_squat: BarbellBackSquatExercise,
  barbell_calf_raise: BarbellCalfRaiseExercise,
  cable_calf_raise: CableCalfRaiseExercise,
  bench_dip: BenchDipExercise,
};


export function createExercise(key) {
  const Cls = Exercises[key];
  if (!Cls) throw new Error("Unknown exercise: " + key);
  return new Cls();
}