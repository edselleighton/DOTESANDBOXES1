# Paper Club implementation

The selected design uses warm paper textures, ivory sheets, sage controls,
ink typography, blue/coral players, and a board with an aligned match sidebar.
The desktop interface is moving to PySide6/Qt while preserving the existing rules
and AI strategies. Work proceeds in the following dependency order.

## Progress

- [x] Separate the rules model from drawing and introduce the Qt application shell.
- [x] Build the Paper Club visual foundation, welcome screen, and combined match setup.
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
`python main.py --paper-club` opens the Qt interface. Play opens match setup;
Start match launches the configured existing game while the Qt board is built. The shell supports resizing, maximized startup, F11 fullscreen,
and Escape to leave fullscreen; window preference persistence comes with Settings.

Verification: 25 automated checks cover rules, complete games at all three AI
difficulties, callback cancellation, reset/undo, Tkinter integration, and Qt
layout/fullscreen/launch behavior. Dependency consistency and Python compilation
checks also pass. The Qt shell has been visually inspected with the offscreen
renderer supplied a Windows system font.

## Completed welcome and setup — October 20, 2026

Added the Paper Club tabletop background, layered paper surfaces, openly licensed
Fredoka heading font, consistent native controls, responsive welcome screen, and
combined opponent/difficulty/player-name setup. Decorative illustration hides in
compact windows so the task controls retain room. The selected mode is explicit,
AI difficulty descriptions match the existing strategies, player names survive
opponent switches, and Enter can start a valid match from the name fields.

Setup choices use atomic writes in the versioned local settings file, preserving
other settings. Missing, damaged, or unwritable preferences do not prevent play.
The configured match handoff preserves mode, difficulty, and player names in the
existing game's controller and window title. No change to the AI strategies.

The earlier Windows environment block has cleared. All 42 automated checks pass,
including preference round trips, failure handling, keyboard input, launch
arguments, and layouts at compact, normal, and wide sizes. Visual inspection
covers both new screens. The nine flow/layout checks also pass independently at
150% and 200% display scaling.

## Next increment

Build the responsive Qt game board and aligned match sidebar, with turn/thinking
indicators, named scores, boxes remaining, edge preview, keyboard interaction,
and pause/resume. Keep the completed welcome/setup flow and shared game rules.
