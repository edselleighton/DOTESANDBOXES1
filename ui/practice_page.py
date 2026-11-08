"""The illustrated instructions exercise: close one box on a real board.

The exercise shares the rules model and the Paper Club board so that what a
player learns here matches a match exactly. Only the missing fourth side is
applied, so the position stays the lesson it was set up to be, and the run is
recorded as practice rather than as a ranked result.
"""

from uuid import uuid4

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from core.game_engine import GameEngine, Move
from ui.paper_style import PaperSurface, button, label
from ui.paper_art import paper_icon
from ui.qt_board import GameBoard
from utils.high_scores import PracticeRecord, today

GOAL = Move("col", (3, 2))
# One unrelated edge, then three sides of the middle box: an even number of
# moves leaves the learner as player one, and placing the distant edge first
# keeps the last-move marker on the box the exercise is about. Seeded through
# the rules model, so no board state is written by hand.
SETUP = (Move("row", (0, 0)), Move("row", (2, 2)), Move("col", (2, 2)), Move("row", (2, 3)))
NAMES = ("You", "Board")


class _BoardFrame(QWidget):
    """Hold the shared board at a square size inside a flexible column."""

    def __init__(self, board):
        super().__init__()
        self.board = board
        board.setParent(self)
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def resizeEvent(self, event):
        side = max(1, min(self.width(), self.height()))
        self.board.setGeometry((self.width() - side) // 2, (self.height() - side) // 2,
                               side, side)
        super().resizeEvent(event)


class PracticePage(QWidget):
    back_requested = Signal()
    completed = Signal(object)

    def __init__(self):
        super().__init__()
        self.engine = GameEngine()
        self.attempts = 0
        self.finished = False
        self._run_id = ""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        self.sheet = PaperSurface()
        self.sheet.setMaximumWidth(940)
        body = QVBoxLayout(self.sheet)
        body.setContentsMargins(36, 24, 36, 32)
        body.setSpacing(14)

        heading_row = QHBoxLayout()
        self.back_button = button("Back", "quiet")
        self.back_button.setIcon(paper_icon("book"))
        self.back_button.setAccessibleDescription("Return to the illustrated instructions")
        self.back_button.clicked.connect(self.back_requested)
        heading_row.addWidget(self.back_button)
        heading_row.addWidget(label("Practice: close a box", "heading"), 1)
        body.addLayout(heading_row)

        self.content = QWidget()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        self.guidance = label("", "lead")
        self.guidance.setAccessibleName("Exercise guidance")
        content_layout.addWidget(self.guidance)
        self.board = GameBoard(self.engine)
        self.board.move_requested.connect(self.play)
        self.board_frame = _BoardFrame(self.board)
        content_layout.addWidget(self.board_frame, 1)
        self.counter = label("")
        self.counter.setAccessibleName("Attempts used")
        content_layout.addWidget(self.counter)
        self.keyboard_help = label("Arrows choose an edge · H / V changes direction · "
                                   "Enter draws it · Tab reaches the controls")
        content_layout.addWidget(self.keyboard_help)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; }"
                                  " QScrollArea > QWidget > QWidget { background: transparent; }")
        self.scroll.setWidget(self.content)
        body.addWidget(self.scroll, 1)

        footer = QHBoxLayout()
        footer.setSpacing(10)
        self.reveal_button = button("Show the missing side")
        self.reveal_button.setIcon(paper_icon("hint"))
        self.reveal_button.setAccessibleDescription("Mark the fourth side without drawing it")
        self.reveal_button.clicked.connect(self.reveal)
        self.restart_button = button("Start over", "quiet")
        self.restart_button.setIcon(paper_icon("undo"))
        self.restart_button.setAccessibleDescription("Set the exercise up again from the beginning")
        self.restart_button.clicked.connect(self.prepare)
        self.done_button = button("Done", "primary")
        self.done_button.setMinimumWidth(180)
        self.done_button.clicked.connect(self.back_requested)
        footer.addWidget(self.reveal_button)
        footer.addWidget(self.restart_button)
        footer.addStretch()
        footer.addWidget(self.done_button)
        body.addLayout(footer)
        outer.addWidget(self.sheet, alignment=Qt.AlignmentFlag.AlignHCenter)
        QWidget.setTabOrder(self.board, self.reveal_button)
        QWidget.setTabOrder(self.reveal_button, self.restart_button)
        QWidget.setTabOrder(self.restart_button, self.done_button)
        self.prepare()

    def set_motion_policy(self, policy):
        self.board.set_motion_policy(policy)

    def prepare(self):
        """Set the one-box position up again and begin a fresh recorded run."""
        self.board.finish_feedback()
        self.engine.reset()
        for move in SETUP:
            self.engine.play(move)
        self.attempts = 0
        self.finished = False
        self._run_id = uuid4().hex
        self.board.selected = GOAL
        self.board.keyboard_selection = False
        self._refresh()
        self.board.setFocus()

    def play(self, move):
        """Apply only the missing fourth side; other edges count as an attempt."""
        if self.finished or self.board.animating or not self.engine.is_legal(move):
            return None
        self.attempts += 1
        if move != GOAL:
            self._refresh("That edge is open, but it does not close the middle box. "
                          "Look for the side that is still missing.")
            return None
        outcome = self.engine.play(move)
        self.finished = True
        self._refresh()
        self.board.animate_move(outcome)
        record = PracticeRecord(self._run_id, self.attempts, today())
        self.completed.emit(record)
        self.done_button.setFocus()
        return outcome

    def reveal(self):
        if not self.finished:
            self.board.show_hint(GOAL)

    def _refresh(self, note=""):
        if self.finished:
            self.guidance.setText("That box is yours, and a capture earns another turn. "
                                  "In a match you would draw again straight away.")
        else:
            self.guidance.setText(note or "Three sides of the middle box are drawn. "
                                  "Draw its fourth side to claim it.")
        attempts = (f"Closed in {self.attempts} "
                    f"{'attempt' if self.attempts == 1 else 'attempts'}." if self.finished
                    else f"Attempts: {self.attempts}")
        self.counter.setText(attempts)
        self.counter.setAccessibleName(attempts)
        self.reveal_button.setEnabled(not self.finished)
        self.restart_button.setText("Try again" if self.finished else "Start over")
        self.board.refresh(not self.finished, False, NAMES)

    def hideEvent(self, event):
        self.board.finish_feedback()
        super().hideEvent(event)

    def resizeEvent(self, event):
        compact = self.height() < 620 or self.width() < 900
        self.sheet.setFixedWidth(min(940, max(1, self.width() - 32)))
        self.sheet.setFixedHeight(max(1, self.height() - 32))
        self.sheet.layout().setContentsMargins(24 if compact else 36, 18 if compact else 24,
                                               24 if compact else 36, 24 if compact else 32)
        self.sheet.layout().setSpacing(8 if compact else 14)
        self.keyboard_help.setVisible(not compact)
        self.board_frame.setMinimumHeight(200 if compact else 280)
        super().resizeEvent(event)
