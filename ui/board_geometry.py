"""Presentation-only coordinates using the original board's edge hit areas."""

from dataclasses import dataclass
from math import floor, isfinite

from core.game_engine import DOT_COUNT, Move


@dataclass(frozen=True)
class BoardGeometry:
    size: float

    def __post_init__(self):
        if not isfinite(self.size) or self.size <= 0:
            raise ValueError("Board size must be positive and finite")

    @property
    def spacing(self):
        return self.size / DOT_COUNT

    def hit_test(self, x: float, y: float) -> Move | None:
        if not isfinite(x) or not isfinite(y) or not (0 <= x <= self.size and 0 <= y <= self.size):
            return None
        step = self.spacing
        sx = floor((x - step / 4) / (step / 2))
        sy = floor((y - step / 4) / (step / 2))
        if sy % 2 == 0 and sx % 2 == 1:
            px, py = (sx - 1) // 2, sy // 2
            if 0 <= px < DOT_COUNT - 1 and 0 <= py < DOT_COUNT:
                return Move("row", (px, py))
        if sx % 2 == 0 and sy % 2 == 1:
            px, py = sx // 2, (sy - 1) // 2
            if 0 <= px < DOT_COUNT and 0 <= py < DOT_COUNT - 1:
                return Move("col", (px, py))
        return None

    def edge_points(self, move: Move):
        x, y = move.position
        start_x = (x + 0.5) * self.spacing
        start_y = (y + 0.5) * self.spacing
        return (start_x, start_y,
                start_x + (self.spacing if move.edge == "row" else 0),
                start_y + (self.spacing if move.edge == "col" else 0))
