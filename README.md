# Dots and Boxes

A desktop implementation of the classic Dots and Boxes game built with Python.
Paper Club uses PySide6/Qt for a textured paper interface, a responsive board,
and a shared, independently testable rules model. The original Tkinter interface
remains available with `--classic`.

## Features

- Player-versus-player mode
- Player-versus-AI mode
- Difficulty-based AI using random, tactical, and heuristic move selection
- Live score display
- Move hints
- Undo support in player-versus-player games
- Mouse edge preview, keyboard play, and a last-move marker
- Pause/resume, including safe suspension of computer turns
- Fullscreen on first launch, with remembered window preferences
- Short move, capture, button, and screen animations with a saved reduced-motion option
- Illustrated instructions and an in-game display settings panel
- Final-board results with same-settings Rematch

## Requirements

- Python 3.10 or newer
- Tkinter
- pip

Tkinter is included with standard Python installations on Windows. Some Linux distributions provide it as a separate package.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the runtime dependencies:

```powershell
pip install -r requirements.txt
```

## Run

Start the game from the repository root:

```powershell
python main.py
```

Choose **Play**, then select **Computer** or **A friend**, enter names,
and choose an AI difficulty when applicable. Click an available edge between
adjacent dots. Completing a box adds it to your score and gives you another move.

## Paper Club controls

```powershell
python main.py --paper-club
```

`--paper-club` is an alias for the default interface. Setup and window choices
are remembered atomically in `%LOCALAPPDATA%/DotsAndBoxes/settings.json`.
Missing or damaged preferences do not prevent play.

The game opens in true fullscreen on first launch. **F11** toggles fullscreen;
closing the game remembers windowed/fullscreen mode, maximization, and window size.
**Start match** plays in the same window. Wide windows show an aligned player
sidebar; compact windows use a score strip above the board.

- **Arrows** select an edge; **H / V** changes its orientation.
- **Enter / Space** draws the selected edge. **Tab** moves to match controls.
- **Hint** marks a suggested edge without playing it.
- **Undo** reverses the last non-scoring move in two-player games.
- **Pause / Escape** suspends a match and opens Resume, Settings, New game, and
  Home. Minimizing also pauses; restore and resume when ready. Computer moves
  cannot run while paused or after leaving a match.
- **Pause > Home / New game** asks before discarding an unfinished match.
- **Settings > Display > Reduced motion** switches to immediate feedback and remembers
  your choice. Until you choose, Windows animation preferences set the default.
- **Settings > Display > Fullscreen** changes window mode; **F11** does the same.
- **How to play** on the welcome screen opens the illustrated Instructions tab.

Settings opened during a match preserves the board and cancels pending computer
moves. **Done** returns to the pause panel; choose **Resume** to continue.

Captured boxes show player initials (or 1/2 for matching initials), and gold
rings mark the most recent edge. Completed matches retain the final board and
scores together with **Rematch**, **New game**, and **Home**. Rematch starts a clean
board with the same opponent, difficulty, and names. Scores update immediately
while new lines draw and captured boxes fill.
Move input, Hint, and Undo wait briefly for that feedback; Pause stays available.
Computer moves are paced individually, including consecutive captures. Pausing,
leaving a match, or minimizing settles active effects without replaying moves.

Audio, the instructions practice exercise, persistent high scores, personal-best
feedback, and the results celebration are still in progress. The welcome screen's
High scores entry is disabled until score storage is available.
See [the implementation roadmap](ROADMAP.md) for completed and upcoming work.

## Development checks

```powershell
python -m unittest discover -s tests -v
```

The suite covers game rules, AI turn sequencing, invalid clicks, undo, full-match
completion, Tkinter screen wiring, Qt mouse/keyboard input, pause/navigation,
responsive layouts, fullscreen persistence, animation interruption, reduced
motion, and consecutive computer captures. Qt checks run offscreen;
Tkinter checks construct withdrawn windows. Both GUI runtimes must be installed. Preference checks use isolated temporary files.

## AI strategy

The current AI changes its selection rule with the chosen difficulty. Each rule operates on the edges that are still available on the 5-by-5 box board.

### Easy: random selection

Easy builds a list of every unoccupied horizontal and vertical edge, then selects one at random. It does not inspect whether the move completes a box, creates a risk, or improves a later position.

### Medium: immediate-box tactic

Medium scans the boxes in row-and-column order. If a box already has three occupied sides, it selects the missing fourth edge and scores that box. When no box can be completed immediately, Medium falls back to the same random selection used by Easy.

This is a one-step tactical rule. It prioritizes an available score, but it does not compare all legal moves, predict the opponent's reply, or avoid setting up a box for the opponent.

### Hard: heuristic best-move evaluation

Hard evaluates every available edge and selects the edge with the highest numerical score. For each candidate, the hint engine temporarily places the edge, evaluates the resulting board, and then removes the edge so the live game state is unchanged.

The heuristic score uses these exact weights:

```text
+100  if the candidate completes an unclaimed box
 -50  if the resulting board contains an unclaimed three-sided box
 +20  for each unclaimed box with exactly two occupied sides
  +2  when the candidate touches zero occupied sides in adjacent boxes
  +5  when the candidate touches one occupied side in adjacent boxes
  +3  when the candidate touches two occupied sides in adjacent boxes
```

Completing a box receives the strongest single reward. A three-sided box is penalized because its remaining edge may become an easy score. Two-sided boxes and the number of occupied sides around the candidate are lower-weight positional factors used to rank otherwise similar moves.

In this project, **best move** means the legal edge with the highest heuristic score for the board produced by that one move. If multiple edges have the same score, the first one encountered during the board scan is selected. This is not a guarantee of mathematically optimal play.

### Minimax distinction

Minimax would recursively simulate future AI and opponent moves, assume that both players choose their strongest continuation, and work backward from those outcomes. The current implementation does **not** perform that recursive search. Medium uses an immediate completion rule, while Hard uses a one-move heuristic evaluation without simulating an opponent response. Describing the current AI as minimax would therefore be inaccurate.

During a game:

- **HINT** highlights a suggested move.
- **UNDO** reverts the previous non-scoring move in player-versus-player mode.
- In the classic interface, **BACK** returns to mode selection.

## Build the Windows executable

Install the build dependency:

```powershell
pip install -r requirements-dev.txt
```

Build with the tracked PyInstaller specification:

```powershell
pyinstaller DotsAndBoxes.spec
```

The executable is generated at `dist/DotsAndBoxes.exe`. The `build/` and `dist/`
directories are intentionally excluded from version control. Final verification
of the Qt executable and its bundled assets is planned for the packaging milestone;
the current UI milestone is verified from Python source.

## Project structure

```text
assets/             Images used by the interface
core/               UI-independent rules, turn sequencing, hints, and AI
ui/                 Paper Club screens, Qt board, and retained Tkinter interface
tests/              Rules, controller, and desktop integration checks
utils/              Assets, shared constants, and atomic preferences
DotsAndBoxes.spec   PyInstaller build configuration
main.py             Application entry point
```

