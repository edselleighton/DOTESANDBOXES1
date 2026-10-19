# Dots and Boxes

A desktop implementation of the classic Dots and Boxes game built with Python.
The current playable interface uses Tkinter. The Paper Club redesign is being
introduced with a Qt application shell and a shared, independently testable rules model.

## Features

- Player-versus-player mode
- Player-versus-AI mode
- Difficulty-based AI using random, tactical, and heuristic move selection
- Live score display
- Move hints
- Undo support in player-versus-player games

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

Install the runtime dependency:

```powershell
pip install -r requirements.txt
```

## Run

Start the game from the repository root:

```powershell
python main.py
```

Choose **VS PLAYER** for a local two-player game or **VS AI** and select a difficulty. Click an available line between adjacent dots to make a move. Completing a box adds it to the active player's score.

## Paper Club preview

```powershell
python main.py --paper-club
```

The Qt shell opens maximized and supports **F11** fullscreen; **Escape** returns
from fullscreen. During the interface migration, **Play** opens the current
Tkinter game in a separate window. The full Paper Club screens, artwork,
animations, audio, settings, instructions, and high scores are still in progress.
See [the implementation roadmap](ROADMAP.md) for completed and upcoming work.

## Development checks

```powershell
python -m unittest discover -s tests -v
```

The suite covers game rules, AI turn sequencing, invalid clicks, undo, full-match
completion, Tkinter screen wiring, and Qt shell behavior. Qt checks run offscreen;
Tkinter checks construct withdrawn windows. Both GUI runtimes must be installed.

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
- **BACK** returns to mode selection.

## Build the Windows executable

Install the build dependency:

```powershell
pip install -r requirements-dev.txt
```

Build with the tracked PyInstaller specification:

```powershell
pyinstaller DotsAndBoxes.spec
```

The executable is generated at `dist/DotsAndBoxes.exe`. The `build/` and `dist/` directories are intentionally excluded from version control.

## Project structure

```text
assets/             Images used by the interface
core/               UI-independent rules, turn sequencing, hints, and AI
ui/                 Tkinter screens, board rendering, and the Qt shell
tests/              Rules, controller, and desktop integration checks
utils/              Shared constants
DotsAndBoxes.spec   PyInstaller build configuration
main.py             Application entry point
```

