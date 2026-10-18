"""Draw the shared rules model in the existing Tkinter game."""

from core.game_engine import DOT_COUNT, GameEngine, Move
from ui.board_geometry import BoardGeometry

PLAYER_COLORS = {1: "#0492CF", 2: "#EE4035"}
BOX_COLORS = {1: "#67B0CF", 2: "#EE7E77"}


class TkBoardRenderer:
    def __init__(self, canvas, engine: GameEngine, size):
        self.canvas = canvas
        self.engine = engine
        self.geometry = BoardGeometry(size)

    def render(self):
        self.canvas.delete("board")
        self.canvas.delete("hint")
        step = self.geometry.spacing
        edge_width = step * 0.1
        for x in range(DOT_COUNT):
            coordinate = (x + 0.5) * step
            self.canvas.create_line(coordinate, step / 2, coordinate,
                                    self.geometry.size - step / 2,
                                    fill="gray", dash=(2, 2), tags="board")
            self.canvas.create_line(step / 2, coordinate,
                                    self.geometry.size - step / 2, coordinate,
                                    fill="gray", dash=(2, 2), tags="board")
        for x in range(DOT_COUNT - 1):
            for y in range(DOT_COUNT - 1):
                owner = int(self.engine.box_owner[x, y])
                if owner:
                    sx, sy = (x + 0.5) * step, (y + 0.5) * step
                    self.canvas.create_rectangle(sx, sy, sx + step, sy + step,
                                                 fill=BOX_COLORS[owner], outline="",
                                                 tags="board")
        for outcome in self.engine.history:
            self.canvas.create_line(*self.geometry.edge_points(outcome.move),
                                    fill=PLAYER_COLORS[outcome.player],
                                    width=edge_width, tags="board")
        radius = step * 0.125
        for x in range(DOT_COUNT):
            for y in range(DOT_COUNT):
                cx, cy = (x + 0.5) * step, (y + 0.5) * step
                self.canvas.create_oval(cx - radius, cy - radius,
                                        cx + radius, cy + radius,
                                        fill="#7BC043", outline="#7BC043",
                                        tags="board")

    def highlight(self, move: Move):
        self.canvas.delete("hint")
        self.canvas.create_line(*self.geometry.edge_points(move), fill="yellow",
                                width=self.geometry.spacing * 0.1 + 2,
                                dash=(4, 2), tags="hint")
