# Paper Club implementation

The selected design uses warm paper textures, ivory sheets, sage controls,
ink typography, blue/coral players, and a board with an aligned match sidebar.
The desktop interface is moving to PySide6/Qt while preserving the existing rules
and AI strategies. Work proceeds in the following dependency order.

## Progress

- [x] Separate the rules model from drawing and introduce the Qt application shell.
- [x] Build the Paper Club visual foundation, welcome screen, and combined match setup.
- [x] Add the responsive Qt board, match sidebar, keyboard controls, and pause/resume.
- [x] Add move/capture transitions, AI pacing, and reduced-motion support.
- [x] Add Settings, audio controls, original sound effects, and gentle background music.
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

Add the one-box instructions practice exercise and persistent local high scores.
Retain the existing illustrated rules, Settings tabs, safe pause routing, display
controls, audio preferences, and results foundation. Separate ranked and practice
records, exclude abandoned games and the exercise, and use match IDs to avoid
duplicates. This is the next bounded milestone, pending explicit approval.
Wait for the next explicit approval before starting this increment.

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

## Completed motion and feedback — October 24, 2026

Added native Qt feedback: 120 ms button presses, 160 ms ink lines, 220 ms capture
fills, and 180 ms page fades. Scores and ownership update immediately. Board
input, Hint, and Undo wait for the short board effect, while Pause remains
available. Consecutive computer captures are individually paced at 300 ms,
retaining the controller's cancellation and stale-callback protection.

View > Reduced motion is available now and persists atomically alongside other
preferences. Windows client-area animation preferences supply the initial default
until overridden. Reduced motion, pause, navigation, hiding, and minimizing settle
active effects; restoration never replays old moves. Button feedback preserves
native keyboard activation, focus, hit targets, and checked/disabled states.

Verification: all 94 automated checks pass, including the full rules and real-AI
regression suite, complete animated games, immediate capture scores, input gates,
rapid navigation, minimized cleanup, and preference persistence. All 17 motion
and control checks also pass at 150% and 200% scaling. Dependency, compilation,
and whitespace checks pass. Actual intermediate capture frames and the compact
paused layout were visually inspected. Forty offscreen board captures averaged
2.37 ms (3.71 ms maximum); this is a local drawing diagnostic, not a display
frame-rate guarantee. The earlier approval-service limit has cleared.

This completes only the motion increment. Settings/audio, instructions/high
scores, final results, and final packaging remain pending.

## Mockup alignment correction — October 25, 2026

At the user's request, refined the welcome, match, and results composition to
follow the selected Paper Club reference more closely. The welcome now uses
overlapping ivory sheets, a large blue/sage/coral wordmark, a tilted sample board,
and Play followed by How to play, High scores, and Settings. Shared controls and
paper surfaces have consistent spacing, outlines, and readable color contrast.

Removed the persistent toolbar and menu bar. Active matches show only Hint, Undo,
and Pause alongside aligned, equal-size avatars, named scores, a sage turn banner,
and a box-count illustration. Home, New game, and Settings belong in a modal pause
panel with keyboard focus contained inside it. Fullscreen and reduced motion are
in Settings, and F11 remains available. Opening and closing Settings preserves
the match and returns to an explicit Resume action before AI can continue.

Added illustrated rules under How to play and Settings > Instructions. Completed
games keep their final board beside the winner and scores, with same-settings
Rematch, New game, and Home. High scores remains visibly disabled with an
explanation; there are no placeholder audio controls or invented personal bests.

This is a visual/navigation correction, not completion of the remaining audio,
practice/high-score, results-celebration, or packaging milestones. These remain
unchecked above and still require approval before the next increment.

Verification: all 101 automated checks pass, including real AI games, motion,
pause/settings cancellation, keyboard focus containment, navigation confirmation,
long player names, and completed-match rematches. All 31 welcome/setup, match,
and navigation checks pass at 150% and 200% scaling. Actual Qt renders were
inspected at 800 by 480, 1180 by 780, and 1920 by 1080, covering the welcome,
match, results, settings, instructions, and pause screens. Dependency consistency,
Python compilation, and whitespace checks pass. Executable packaging and testing
with an actual screen reader remain part of the final verification milestone.

## Completed audio and display settings — October 27, 2026

Extended the Paper Club Settings panel with independent music/effect sliders,
mute controls, a capture-sound sample, and stronger board contrast. Defaults are
15% music and 50% effects. Sliders, checkboxes, and display switches retain native
keyboard operation and accessible names. Short windows scroll the panel contents
while retaining the Done and Quit controls. Settings still preserves and pauses
the current match until an explicit Resume action.

Added an original 24-second, eight-bar music loop and short move, capture, menu,
and result sounds. All five PCM WAV files are synthesized by the checked-in
Python/NumPy generator, with no sampled recordings. The music loop wraps release
tails across its boundary; effect tails taper to zero. Accepted moves alone emit
game sounds, and the last move emits one result sound. Volume changes apply live
and save atomically after a short debounce or before closing Settings/the game.
Mute keeps each channel's volume. Missing files or unavailable audio output show
an explanation in Settings and leave play available. Minimizing stops all audio;
restoring resumes enabled music and leaves gameplay paused without replaying old
effects. Native Qt sound objects are reused across moves.

Stronger contrast darkens open edges and increases player-line weight without
changing board state, ownership initials, hit targets, or the rules. It persists
in the existing versioned settings file alongside other display preferences.

Verification: all 113 automated checks pass, covering the existing rules/real-AI
games and animations, audio event routing, independent mute/volume, atomic
preferences, output/file failures, minimized cleanup, contrast, and compact
keyboard access. The 19 audio/navigation checks pass at 150% and 200% scaling.
Qt's real audio backend loaded all five WAVs, started looping music and an effect,
and stopped all playback on suspension. PCM checks confirm headroom, tapered
effects, and a music-loop boundary within the ordinary waveform changes.
Actual Settings and stronger-contrast board renders were visually inspected.
Python compilation, dependency consistency, and whitespace checks pass.

This completes the audio/display milestone only. Practice/high scores,
personal-best feedback and celebration, and final executable packaging remain.
The original evening check-in window ended October 25; further work awaits the
user's next approval and a revised pacing preference.
