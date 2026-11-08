"""The high scores sheet: completed matches and the practice exercise."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget,
)

from ui.paper_style import BLUE, PaperSurface, button, label
from ui.paper_art import paper_icon


class _Row(QWidget):
    """One ranked entry, readable as a single line by assistive tools."""

    def __init__(self, place, record):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(14)
        rank = label(f"{place}.", "fieldLabel")
        rank.setFixedWidth(34)
        rank.setStyleSheet(f"color: {BLUE}; font-size: 17px; font-weight: 700;")
        name = label(record.name, "fieldLabel")
        name.setStyleSheet("font-size: 17px; font-weight: 600;")
        detail = label(f"vs {record.opponent_label} · {record.completed_on}")
        score = label(f"{record.boxes} – {record.opponent_boxes}", "fieldLabel")
        score.setStyleSheet("font-size: 17px; font-weight: 700;")
        score.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        score.setFixedWidth(96)
        copy = QVBoxLayout()
        copy.setSpacing(2)
        copy.addWidget(name)
        copy.addWidget(detail)
        layout.addWidget(rank)
        layout.addLayout(copy, 1)
        layout.addWidget(score)
        self.setAccessibleName(
            f"{place}. {record.name} claimed {record.boxes} boxes to "
            f"{record.opponent_boxes} against {record.opponent_label} on {record.completed_on}.")


class HighScoresPage(QWidget):
    back_requested = Signal()
    practice_requested = Signal()

    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        self.sheet = PaperSurface()
        self.sheet.setMaximumWidth(940)
        body = QVBoxLayout(self.sheet)
        body.setContentsMargins(36, 24, 36, 32)
        body.setSpacing(14)
        heading_row = QHBoxLayout()
        self.back_button = button("Back", "quiet")
        self.back_button.setIcon(paper_icon("home"))
        self.back_button.setAccessibleDescription("Return to the welcome screen")
        self.back_button.clicked.connect(self.back_requested)
        heading_row.addWidget(self.back_button)
        heading_row.addWidget(label("High scores", "heading"), 1)
        body.addLayout(heading_row)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(10)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; }"
                                  " QScrollArea > QWidget > QWidget { background: transparent; }")
        self.scroll.setWidget(self.content)
        body.addWidget(self.scroll, 1)

        footer = QHBoxLayout()
        self.practice_button = button("Practice closing a box")
        self.practice_button.setIcon(paper_icon("book"))
        self.practice_button.clicked.connect(self.practice_requested)
        footer.addWidget(self.practice_button)
        footer.addStretch()
        self.done_button = button("Done", "primary")
        self.done_button.setMinimumWidth(180)
        self.done_button.clicked.connect(self.back_requested)
        footer.addWidget(self.done_button)
        body.addLayout(footer)
        outer.addWidget(self.sheet, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.refresh((), None)

    def refresh(self, ranked, best_practice):
        """Rebuild the sheet from stored records; an empty table says so plainly."""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                # Unparent before deleting; a widget awaiting deletion would
                # otherwise keep painting over the rebuilt sheet.
                widget.setParent(None)
                widget.deleteLater()
        heading = label("Completed matches", "fieldLabel")
        heading.setStyleSheet("font-size: 16px; font-weight: 700;")
        self.content_layout.addWidget(heading)
        self.rows = ()
        self.ranked_message = None
        if ranked:
            self.rows = tuple(_Row(place, record) for place, record in enumerate(ranked, start=1))
            for row in self.rows:
                self.content_layout.addWidget(row)
        else:
            self.ranked_message = label(
                "No finished matches yet. A match counts once all 25 boxes are claimed; "
                "a match you leave early is not recorded.")
            self.content_layout.addWidget(self.ranked_message)
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #D7CCB7;")
        self.content_layout.addWidget(divider)
        practice_heading = label("Practice: closing a box", "fieldLabel")
        practice_heading.setStyleSheet("font-size: 16px; font-weight: 700;")
        self.content_layout.addWidget(practice_heading)
        if best_practice is None:
            practice = label("The instructions exercise has not been completed yet. "
                             "Practice runs are kept apart from completed matches.")
        else:
            attempts = "attempt" if best_practice.attempts == 1 else "attempts"
            practice = label(f"Best run: {best_practice.attempts} {attempts} "
                             f"on {best_practice.completed_on}. "
                             f"Practice runs are kept apart from completed matches.")
        practice.setAccessibleName(practice.text())
        self.practice_summary = practice
        self.content_layout.addWidget(practice)
        self.content_layout.addStretch()

    def resizeEvent(self, event):
        compact = self.height() < 620 or self.width() < 900
        self.sheet.setFixedWidth(min(940, max(1, self.width() - 32)))
        self.sheet.setFixedHeight(max(1, self.height() - 32))
        self.sheet.layout().setContentsMargins(24 if compact else 36, 18 if compact else 24,
                                               24 if compact else 36, 24 if compact else 32)
        self.sheet.layout().setSpacing(8 if compact else 14)
        super().resizeEvent(event)
