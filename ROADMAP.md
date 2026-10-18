# Paper Club implementation

The selected design uses warm paper textures, ivory sheets, sage controls,
ink typography, blue/coral players, and a board with an aligned match sidebar.
The desktop interface is moving to PySide6/Qt while preserving the existing rules
and AI strategies. Work proceeds in the following dependency order.

## Progress

- [x] Separate the rules model from drawing and introduce the Qt application shell.
- [ ] Build the Paper Club visual foundation, welcome screen, and combined match setup.
- [ ] Add the responsive Qt board, match sidebar, keyboard controls, and pause/resume.
- [ ] Add move/capture transitions, AI pacing, and reduced-motion support.
- [ ] Add Settings, audio controls, original sound effects, and gentle background music.
- [ ] Add illustrated instructions, practice, and persistent local high scores.
- [ ] Finish results, personal-best feedback, same-settings rematches, and celebration.
- [ ] Complete visual/accessibility checks, end-to-end verification, and Windows packaging.

## Completed foundation — October 19, 2026

The rules model owns NumPy occupancy/ownership arrays, turns, scores, captures,
history, and reset/undo. `MoveOutcome` reports only the boxes captured by that move.
`MatchConfig` carries mode, difficulty, and player names. Existing AI and hint
selection strategies retain their original implementations and weights.

The shared match controller accepts UI scheduling functions and emits move and
completion callbacks. It blocks input on AI turns, allows only one pending AI
move, rejects callbacks from old matches, and stops after completion or navigation.
Coordinates live in presentation-only board geometry, which rejects margins and
invalid indices before they can reach the rules model.

The existing game now uses this model/controller through a Tkinter renderer.
Its launcher remains the default while the Qt gameplay screens are introduced.
`python main.py --paper-club` opens the Qt shell, whose Play action launches the
existing game. The shell supports resizing, maximized startup, F11 fullscreen,
and Escape to leave fullscreen; window preference persistence comes with Settings.

Verification: 25 automated checks cover rules, complete games at all three AI
difficulties, callback cancellation, reset/undo, Tkinter integration, and Qt
layout/fullscreen/launch behavior. Dependency consistency and Python compilation
checks also pass. The Qt shell has been visually inspected with the offscreen
renderer supplied a Windows system font.

## Next increment

Create the reusable Paper Club visual controls and surfaces, welcome screen, and
combined opponent/difficulty/player-name setup. Keep gameplay accessible through
the current interface until the Qt board is ready. Later features remain unchecked
until implemented and verified.
