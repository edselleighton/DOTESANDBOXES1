"""Dots and Boxes rules, independent of any window or drawing toolkit.

For compatibility with the existing AI, ``row[x, y]`` is a horizontal edge
and ``col[x, y]`` is a vertical edge. Both occupancy arrays contain only 0/1.
"""

from dataclasses import dataclass
from numbers import Integral
from typing import Literal

import numpy as np

from core.ai_engine import AIEngine
from core.hint_engine import HintEngine

DOT_COUNT = 6


@dataclass(frozen=True)
class MatchConfig:
    mode: Literal["PVP", "AI"] = "PVP"
    difficulty: Literal["easy", "medium", "hard"] | None = None
    player_names: tuple[str, str] = ("Player 1", "Player 2")

    def __post_init__(self):
        if self.mode not in ("PVP", "AI"):
            raise ValueError("Mode must be PVP or AI")
        if self.mode == "AI" and self.difficulty is None:
            object.__setattr__(self, "difficulty", "medium")
        if self.difficulty not in (None, "easy", "medium", "hard"):
            raise ValueError("Unknown AI difficulty")
        if len(self.player_names) != 2 or any(
            not isinstance(name, str) or not name.strip() for name in self.player_names
        ):
            raise ValueError("Two non-empty player names are required")


@dataclass(frozen=True)
class Move:
    edge: Literal["row", "col"]
    position: tuple[int, int]


@dataclass(frozen=True)
class MoveOutcome:
    move: Move
    player: int
    captured_boxes: tuple[tuple[int, int], ...]
    scores: tuple[int, int]
    next_player: int
    finished: bool


class GameEngine:
    def __init__(self):
        self.row_status = np.zeros((DOT_COUNT - 1, DOT_COUNT), dtype=np.int8)
        self.col_status = np.zeros((DOT_COUNT, DOT_COUNT - 1), dtype=np.int8)
        self.box_owner = np.zeros((DOT_COUNT - 1, DOT_COUNT - 1), dtype=np.int8)
        self.player1_turn = True
        self._history: list[MoveOutcome] = []
        self.hints = HintEngine(self)
        self.ai = AIEngine(self)

    @property
    def current_player(self):
        return 1 if self.player1_turn else 2

    @property
    def scores(self):
        return (
            int(np.count_nonzero(self.box_owner == 1)),
            int(np.count_nonzero(self.box_owner == 2)),
        )

    @property
    def finished(self):
        return bool(np.all(self.box_owner != 0))

    @property
    def history(self):
        return tuple(self._history)

    @property
    def can_undo(self):
        return bool(self._history and not self._history[-1].captured_boxes)

    def reset(self):
        self.row_status.fill(0)
        self.col_status.fill(0)
        self.box_owner.fill(0)
        self._history.clear()
        self.player1_turn = True

    def is_legal(self, move: Move):
        if not isinstance(move, Move) or move.edge not in ("row", "col"):
            return False
        if not isinstance(move.position, tuple) or len(move.position) != 2:
            return False
        if any(not isinstance(value, Integral) or isinstance(value, bool)
               for value in move.position):
            return False
        x, y = move.position
        edges = self.row_status if move.edge == "row" else self.col_status
        return (not self.finished and 0 <= x < edges.shape[0]
                and 0 <= y < edges.shape[1] and edges[x, y] == 0)

    def play(self, move: Move) -> MoveOutcome | None:
        """Apply one legal edge; an invalid or occupied edge changes nothing."""
        if not self.is_legal(move):
            return None

        player = self.current_player
        x, y = move.position
        edges = self.row_status if move.edge == "row" else self.col_status
        edges[x, y] = 1
        captured = []
        for bx in range(DOT_COUNT - 1):
            for by in range(DOT_COUNT - 1):
                if self.box_owner[bx, by] != 0:
                    continue
                if (self.row_status[bx, by] and self.row_status[bx, by + 1]
                        and self.col_status[bx, by] and self.col_status[bx + 1, by]):
                    self.box_owner[bx, by] = player
                    captured.append((bx, by))

        if not captured:
            self.player1_turn = not self.player1_turn
        outcome = MoveOutcome(move, player, tuple(captured), self.scores,
                              self.current_player, self.finished)
        self._history.append(outcome)
        return outcome

    def undo_move(self):
        """Revert the last non-scoring move, including its original player."""
        if not self.can_undo:
            return False
        outcome = self._history.pop()
        edges = self.row_status if outcome.move.edge == "row" else self.col_status
        edges[outcome.move.position] = 0
        self.player1_turn = outcome.player == 1
        return True

    def get_hint(self) -> Move | None:
        suggestion = self.hints.get_best_move()
        return Move(*suggestion) if suggestion is not None else None

    def ai_move(self, difficulty: str) -> MoveOutcome | None:
        if self.finished:
            return None
        suggestion = self.ai.get_ai_move(difficulty)
        return self.play(Move(*suggestion)) if suggestion is not None else None
