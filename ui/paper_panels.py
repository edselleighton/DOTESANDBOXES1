"""Paper panels for display preferences, rules, and paused-match navigation."""

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractButton, QDialog, QHBoxLayout, QScrollArea, QStackedWidget, QTabBar,
    QVBoxLayout, QWidget,
)

from ui.paper_style import BLUE, CORAL, INK, SAGE, PaperSurface, button, label
from ui.paper_art import paper_icon


class Switch(QAbstractButton):
    """A native keyboard-operable toggle with an explicit accessible name."""
    def __init__(self, name):
        super().__init__()
        self.setCheckable(True)
        self.setAccessibleName(name)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedSize(76, 48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(SAGE if self.isChecked() else "#C5C0B3"))
        painter.drawRoundedRect(QRectF(7, 9, 62, 30), 15, 15)
        painter.setBrush(QColor(65, 48, 25, 35))
        x = 41 if self.isChecked() else 9
        painter.drawEllipse(QRectF(x + 1, 12, 26, 26))
        painter.setBrush(QColor("#FFFCF4"))
        painter.drawEllipse(QRectF(x, 11, 26, 26))
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(BLUE), 2))
            painter.drawRoundedRect(QRectF(2, 3, 72, 42), 19, 19)


class RuleDrawing(QWidget):
    def __init__(self, step):
        super().__init__()
        self.step = step
        self.setFixedSize(88, 76)
        self.setAccessibleName(("Join two neighboring dots", "Complete the fourth side",
                                "Claim the box and play again")[step])

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        points = [QPointF(20, 14), QPointF(68, 14), QPointF(68, 62), QPointF(20, 62)]
        if self.step == 2:
            p.fillRect(QRectF(20, 14, 48, 48), QColor("#D0E3ED"))
        p.setPen(QPen(QColor("#CFC2A7"), 1))
        p.drawRect(QRectF(20, 14, 48, 48))
        for index in range(1 if self.step == 0 else 4):
            p.setPen(QPen(QColor(CORAL if index == 3 and self.step == 1 else BLUE), 4,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(points[index], points[(index + 1) % 4])
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(INK))
        for point in points:
            p.drawEllipse(point, 4, 4)


class SettingsPage(QWidget):
    done_requested = Signal()
    exit_requested = Signal()
    fullscreen_changed = Signal(bool)
    reduced_motion_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.addStretch()
        self.sheet = PaperSurface()
        self.sheet.setMaximumWidth(940)
        body = QVBoxLayout(self.sheet)
        body.setContentsMargins(44, 28, 44, 36)
        body.setSpacing(20)
        body.addWidget(label("Settings", "heading"))
        self.tabs = QTabBar()
        self.tabs.setExpanding(False)
        self.tabs.setAccessibleName("Settings sections")
        self.tabs.addTab(paper_icon("settings"), "Display")
        self.tabs.addTab(paper_icon("book"), "Instructions")
        self.tabs.setStyleSheet("""
            QTabBar::tab { background: #F1E8D8; color: #20394A; border: 1px solid #CBBDA3;
                border-top-left-radius: 8px; border-top-right-radius: 8px;
                padding: 12px 24px; min-height: 24px; font-weight: 600; }
            QTabBar::tab:selected { background: #617B55; color: white; border-color: #617B55; }
            QTabBar::tab:focus { border: 2px solid #265A80; padding: 11px 23px; }
        """)
        body.addWidget(self.tabs)
        self.content = QStackedWidget()
        self.display = QWidget()
        display_layout = QVBoxLayout(self.display)
        display_layout.setContentsMargins(12, 12, 12, 12)
        display_layout.setSpacing(28)
        self.fullscreen = Switch("Fullscreen")
        self.reduced_motion = Switch("Reduced motion")
        for text, note, switch in (
            ("Fullscreen", "Fill the screen with your tabletop. F11 also switches modes.", self.fullscreen),
            ("Reduced motion", "Show moves immediately with no animated transitions.", self.reduced_motion),
        ):
            row = QHBoxLayout()
            copy = QVBoxLayout()
            copy.setSpacing(6)
            title = label(text, "fieldLabel")
            title.setStyleSheet("font-size: 18px; font-weight: 600;")
            copy.addWidget(title)
            copy.addWidget(label(note))
            row.addLayout(copy, 1)
            row.addWidget(switch)
            display_layout.addLayout(row)
        display_layout.addStretch()
        self.instructions = QWidget()
        rules = QVBoxLayout(self.instructions)
        rules.setContentsMargins(0, 0, 0, 0)
        rules.setSpacing(8)
        for step, heading, detail in (
            (0, "1. Draw a line", "Choose an open edge between two neighboring dots. Take turns."),
            (1, "2. Close a box", "Draw its fourth side to claim the box and score one point."),
            (2, "3. Keep your turn", "After a capture, play again. Claim the most of the 25 boxes to win."),
        ):
            row = QHBoxLayout()
            row.addWidget(RuleDrawing(step))
            copy = QVBoxLayout()
            copy.addWidget(label(heading, "fieldLabel"))
            copy.addWidget(label(detail))
            row.addLayout(copy, 1)
            rules.addLayout(row)
        rules.addWidget(label("Keyboard: arrows choose an edge · H / V changes direction · Enter / Space draws.\n"
                              "Tab reaches controls · Escape pauses · Undo removes the last non-scoring move in two-player games."))
        self.content.addWidget(self.display)
        self.rules_scroll = QScrollArea()
        self.rules_scroll.setWidgetResizable(True)
        self.rules_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollArea > QWidget > QWidget { background: transparent; }")
        self.rules_scroll.setWidget(self.instructions)
        self.content.addWidget(self.rules_scroll)
        self.tabs.currentChanged.connect(self.content.setCurrentIndex)
        self.tabs.currentChanged.connect(self._arrange)
        body.addWidget(self.content, 1)
        footer = QHBoxLayout()
        self.exit_button = button("Quit game", "quiet")
        self.exit_button.clicked.connect(self.exit_requested)
        footer.addWidget(self.exit_button)
        footer.addStretch()
        self.done_button = button("Done", "primary")
        self.done_button.setMinimumWidth(200)
        self.done_button.clicked.connect(self.done_requested)
        footer.addWidget(self.done_button)
        body.addLayout(footer)
        outer.addWidget(self.sheet, alignment=Qt.AlignmentFlag.AlignHCenter)
        outer.addStretch()
        self.fullscreen.toggled.connect(self.fullscreen_changed)
        self.reduced_motion.toggled.connect(self.reduced_motion_changed)

    def _arrange(self, *_):
        self.sheet.setFixedWidth(min(940, max(1, self.width() - 32)))
        self.sheet.layout().setContentsMargins(28, 20, 28, 24)
        self.sheet.layout().setSpacing(12 if self.height() < 620 else 20)
        height = 480 if self.tabs.currentIndex() == 0 else 640
        self.sheet.setFixedHeight(min(height, max(1, self.height() - 32)))

    def resizeEvent(self, event):
        self._arrange()
        super().resizeEvent(event)


class PausePanel(QDialog):
    resume_requested = Signal()
    settings_requested = Signal()
    new_requested = Signal()
    home_requested = Signal()

    def __init__(self, parent):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Match paused")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(400)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        sheet = PaperSurface()
        body = QVBoxLayout(sheet)
        body.setContentsMargins(32, 28, 32, 36)
        body.setSpacing(12)
        title = label("A little break.", "heading")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(title)
        self.explanation = label("Your board is right where you left it.")
        self.explanation.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(self.explanation)
        body.addSpacing(8)
        self.resume = button("Resume", "primary")
        self.settings = button("Settings", "quiet")
        self.new_game = button("New game", "quiet")
        self.home = button("Home", "quiet")
        for control, icon, signal in (
            (self.resume, "play", self.resume_requested),
            (self.settings, "settings", self.settings_requested),
            (self.new_game, "play", self.new_requested),
            (self.home, "home", self.home_requested),
        ):
            control.setIcon(paper_icon(icon, "#FFFFFF" if control is self.resume else INK))
            control.setIconSize(QSize(22, 22))
            control.clicked.connect(signal)
            body.addWidget(control)
        outer.addWidget(sheet)

    def reject(self):
        self.resume_requested.emit()

    def showEvent(self, event):
        self.adjustSize()
        center = self.parentWidget().frameGeometry().center()
        self.move(center - self.rect().center())
        super().showEvent(event)
        self.resume.setFocus()
