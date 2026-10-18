"""Turn sequencing shared by desktop interfaces; scheduling is supplied by the UI."""

from collections.abc import Callable

from core.game_engine import GameEngine, MatchConfig, Move, MoveOutcome


class MatchController:
    def __init__(self, engine: GameEngine, schedule: Callable, cancel: Callable,
                 on_move: Callable, on_finished: Callable, ai_delay_ms=300):
        self.engine = engine
        self._schedule = schedule
        self._cancel = cancel
        self._on_move = on_move
        self._on_finished = on_finished
        self._ai_delay_ms = ai_delay_ms
        self.config = MatchConfig()
        self.active = False
        self._generation = 0
        self._pending = None

    @property
    def accepts_human_move(self):
        return (self.active and not self.engine.finished
                and (self.config.mode == "PVP" or self.engine.current_player == 1))

    @property
    def can_undo(self):
        return self.active and self.config.mode == "PVP" and self.engine.can_undo

    def start(self, config: MatchConfig):
        self.stop()
        self.config = config
        self.engine.reset()
        self.active = True
        self._on_move(None)

    def stop(self):
        self.active = False
        self._generation += 1
        if self._pending is not None:
            self._cancel(self._pending)
            self._pending = None

    def play_human(self, move: Move):
        if not self.accepts_human_move:
            return None
        return self._play(lambda: self.engine.play(move))

    def undo_move(self):
        if not self.can_undo or not self.engine.undo_move():
            return False
        self._on_move(None)
        return True

    def get_hint(self):
        return self.engine.get_hint() if self.accepts_human_move else None

    def _play(self, action: Callable[[], MoveOutcome | None]):
        generation = self._generation
        outcome = action()
        if outcome is None:
            return None
        if outcome.finished:
            self.stop()
            finished_generation = self._generation
            self._on_move(outcome)
            if finished_generation == self._generation:
                self._on_finished(outcome)
        else:
            self._on_move(outcome)
            if self.active and generation == self._generation:
                self._queue_ai()
        return outcome

    def _queue_ai(self):
        if (not self.active or self.config.mode != "AI"
                or self.engine.current_player != 2 or self.engine.finished
                or self._pending is not None):
            return
        generation = self._generation

        def run():
            # A canceled callback may already have entered an event queue. It must
            # never clear a newer match's pending handle or mutate its state.
            if generation != self._generation:
                return
            self._pending = None
            if (self.active and self.config.mode == "AI"
                    and self.engine.current_player == 2 and not self.engine.finished):
                self._play(lambda: self.engine.ai_move(self.config.difficulty))

        self._pending = self._schedule(self._ai_delay_ms, run)
