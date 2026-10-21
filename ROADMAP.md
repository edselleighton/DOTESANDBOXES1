# Paper Club implementation

The selected design uses warm paper textures, ivory sheets, sage controls,
ink typography, blue/coral players, and a board with an aligned match sidebar.
The desktop interface is moving to PySide6/Qt while preserving the existing rules
and AI strategies. Work proceeds in the following dependency order.

## Progress

- [x] Separate the rules model from drawing and introduce the Qt application shell.
- [x] Build the Paper Club visual foundation, welcome screen, and combined match setup.
- [x] Add the responsive Qt board, match sidebar, keyboard controls, and pause/resume.
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

The existing game uses this model/controller through a Tkinter renderer.
At this foundation milestone, the classic launcher remained the default and the
Qt preview handed matches to it. The completed board milestone below replaces
that temporary handoff and changes first-launch behavior to true fullscreen.

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

Add restrained move/capture and screen transitions, control feedback, reduced
motion, and animation suspension while minimized. Preserve immediate scoring,
safe input, and the existing one-move-at-a-time computer turn scheduling.

## Completed board and match controls — October 21, 2026

Paper Club is now the default launcher; `--classic` retains the original interface.
Setup starts a Qt match in the same window. The antialiased 6-by-6-dot board shows
ownership initials, hover preview, hint suggestions, and a last-edge marker.
The aligned sidebar displays equal-sized avatars, named scores, the current
player or computer-thinking state, boxes remaining, and clear Hint/Undo reasons.
Compact layouts use a score strip and keep controls reachable at 800 by 480.
The fullscreen board is capped in size, and its header shares the same alignment.

Arrows, H/V, Enter/Space and Tab support keyboard play. Pause/Resume and Escape
suspend input and cancel pending AI callbacks without changing the board. Leaving
a match asks before discarding it; minimizing pauses until explicitly resumed.
Completed games retain their board and scores, with the richer results experience
still reserved for its milestone. AI native-import failures leave a paused,
recoverable match with an explanation; no strategy or OS policy is changed.

Following the user's updated preference, first launch now opens in true fullscreen.
F11 toggles modes, and atomic settings remember fullscreen, maximization, and
window size alongside setup choices. Missing or damaged preferences use defaults.

The selected mockup remains the visual target. Actual Qt renders were inspected at
compact, normal, and fullscreen dimensions; header alignment, sidebar whitespace,
and clipped compact pause text were corrected. Further material/detail refinements
and the remaining screens are still part of the planned overhaul.

Verification: all 71 automated checks pass, including complete local and real
Easy/Medium/Hard computer games, keyboard/mouse interaction, pause/resume and
navigation races, recoverable native-import errors, preference persistence, long
names, and layout boundaries. The 13 Qt match checks also pass at both 150% and
200% scaling. Dependency and Python compilation checks pass. The temporary
Windows Application Control block observed during the interrupted session is no
longer occurring; the final real-AI checks succeeded without policy changes.
