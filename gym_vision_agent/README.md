# Gym Vision AI Agent

A standalone, real-time AI gym trainer powered by **MediaPipe** pose estimation and voice coaching.

## Features

| Feature | Details |
|---|---|
| **18 Exercises** | Squat, Push-up, Bicep Curl, Hammer Curl, Shoulder Press, Lateral Raise, Lunge, Side Lunge, Deadlift, Glute Bridge, Calf Raise, Leg Raise, Plank, Wall Sit, Jumping Jacks, High Knees, Mountain Climbers, Tricep Dip |
| **Rep & Set Counting** | Finite State Machine for accurate, noise-resistant counting |
| **Session Timer** | Elapsed workout time displayed live |
| **Rest Timer** | 60-second rest counter between sets |
| **Initial Posture Check** | Agent verifies your starting position before allowing you to begin |
| **Voice Coaching** | Speaks rep counts, set completions, form corrections, and rest alerts out loud |
| **Real-time Form Feedback** | Joint angles and form errors displayed on screen |

## Installation

```bash
pip install opencv-python mediapipe numpy pyttsx3
```

## Run

```bash
cd gym_vision_agent
python main.py
```

## Controls

### Menu Screen
| Key | Action |
|---|---|
| `↑` / `W` | Move selection up |
| `↓` / `S` | Move selection down |
| `ENTER` | Select exercise |
| `Q` | Quit |

### Config Screen (Reps / Sets)
| Key | Action |
|---|---|
| `A` / `D` | Decrease / increase reps |
| `W` / `S` | Decrease / increase sets |
| `ENTER` | Start workout |
| `ESC` | Back to menu |

### Workout Screen
| Key | Action |
|---|---|
| `SPACE` | Pause / Resume |
| `Q` / `ESC` | Stop workout & return to menu |

## How It Works

1. **Select** your exercise from the menu.
2. **Configure** how many reps and sets you want.
3. **Stand** in front of the camera and hold the starting position. The agent will hold the calibration bar for 2.5 seconds.
4. When the bar fills up, the agent says **"Go!"** and begins counting.
5. Between sets, a **60-second rest timer** is displayed.
6. If your form breaks, the agent **speaks** a correction immediately.






## Further---------

### Gamification of agent

**Combo multiplier** — consecutive clean-form reps build a combo (5/10/15/20+) that multiplies your points, so sloppy reps actually cost you.
**XP & Levels** — every rep earns points based on form quality; leveling up persists across sessions.
**Personal Records** — best reps-in-a-session, best average form, longest combo — tracked per exercise, and it calls out live when you break one.
**Streaks** — consecutive workout days, tracked and announced.
**Local Leaderboard** — multiple players sharing the machine each get a profile; ranked by XP so you can actually compete with a friend.
**Voice hype** — combo milestones, PR breaks, and level-ups get spoken immediately.

followed by gamification.py file.