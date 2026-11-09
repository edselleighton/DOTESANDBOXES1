"""Paper Club welcome and match setup screens."""

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLineEdit, QSizePolicy, QVBoxLayout, QWidget,
)

from ui.paper_style import BoardIllustration, PaperSurface, button, label
from ui.paper_art import PaperLogo, paper_icon
from utils.setup_preferences import SetupChoices


class _WelcomeSheet(PaperSurface):
    """A tilted sheet under real, upright controls, without an enclosing UI card."""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.width() * .045, self.height() * .07,
                      self.width() * .57, self.height() * .89)
        painter.translate(rect.center())
        painter.rotate(-3)
        painter.translate(-rect.center())
        painter.setPen(Qt.PenStyle.NoPen)
        for offset, alpha in ((8, 9), (5, 12), (3, 16)):
            painter.setBrush(QColor(70, 51, 25, alpha))
            painter.drawRoundedRect(rect.translated(2, offset), 13, 13)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor("#FFFCF3"))
        gradient.setColorAt(1, QColor("#F2E5CF"))
        painter.setBrush(gradient)
        painter.setPen(QColor("#DDCDB0"))
        painter.drawRoundedRect(rect, 12, 12)
        path = QPainterPath()
        path.addRoundedRect(rect, 12, 12)
        painter.setClipPath(path)
        painter.drawTiledPixmap(rect, self._grain)


class WelcomePage(QWidget):
    play_requested = Signal()
    instructions_requested = Signal()
    scores_requested = Signal()
    settings_requested = Signal()

    def __init__(self):
        super().__init__()
        self.sheet = _WelcomeSheet(self)
        self.copy = QWidget(self.sheet)
        self.title = PaperLogo(stacked=True, parent=self.copy)
        self.tagline = label("One line can change the game.", "homeTagline")
        self.tagline.setParent(self.copy)
        self.tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tagline.setWordWrap(False)
        self.play_button = button("Play", "primary")
        self.play_button.setParent(self.copy)
        self.play_button.setIcon(paper_icon("play", "#FFFFFF", 24))
        self.play_button.setIconSize(QSize(24, 24))
        self.play_button.setAccessibleDescription("Choose an opponent and set up a match")
        self.play_button.clicked.connect(self.play_requested)
        self.instructions_button = button("How to play", "homeLink")
        self.scores_button = button("High scores", "homeLink")
        self.settings_button = button("Settings", "homeLink")
        for control, icon, signal in (
            (self.instructions_button, "book", self.instructions_requested),
            (self.scores_button, "trophy", self.scores_requested),
            (self.settings_button, "settings", self.settings_requested),
        ):
            control.setParent(self.copy)
            control.setIcon(paper_icon(icon, size=25))
            control.setIconSize(QSize(25, 25))
            control.clicked.connect(signal)
        self.scores_button.setAccessibleDescription(
            "Completed matches and your best practice run")
        self.illustration = BoardIllustration(self.sheet)
        self.setTabOrder(self.play_button, self.instructions_button)
        self.setTabOrder(self.instructions_button, self.scores_button)
        self.setTabOrder(self.scores_button, self.settings_button)

    def resizeEvent(self, event):
        # Preserve the reference's two overlapping sheets even in a short window.
        height = min(self.height(), 860)
        width = min(self.width(), round(height * 1.68), 1440)
        height = min(height, round(width / 1.68))
        self.sheet.setGeometry((self.width() - width) // 2, (self.height() - height) // 2,
                               width, height)
        copy_width = round(width * .41)
        self.copy.setGeometry(round(width * .085), round(height * .105), copy_width, round(height * .86))
        row_height = max(44, min(58, round(height * .078)))
        play_height = max(44, min(66, round(height * .095)))
        tagline_height = max(26, min(40, round(height * .06)))
        available = self.copy.height() - (row_height * 3 + play_height + tagline_height + 16)
        logo_height = max(98, available)
        self.title.setGeometry(0, 0, copy_width, logo_height)
        self.tagline.setGeometry(0, logo_height, copy_width, tagline_height)
        self.tagline.setStyleSheet(f"font-size: {max(14, min(23, round(width / 54)))}px;")
        self.play_button.setStyleSheet(f"font-size: {max(18, min(28, round(width / 48)))}px; font-weight: 600;")
        control_width = round(copy_width * .84)
        left = (copy_width - control_width) // 2
        top = logo_height + tagline_height + 7
        self.play_button.setGeometry(left, top, control_width, play_height)
        top += play_height + 9
        for control in (self.instructions_button, self.scores_button, self.settings_button):
            control.setGeometry(left, top, control_width, row_height)
            control.setStyleSheet(f"font-size: {max(17, min(24, round(width / 55)))}px;")
            top += row_height
        self.illustration.setGeometry(round(width * .49), round(height * .10),
                                      round(width * .50), round(height * .83))
        super().resizeEvent(event)


class SetupPage(QWidget):
    back_requested = Signal()
    start_requested = Signal(object)

    def __init__(self, store):
        super().__init__()
        self.store = store
        choices = store.load()
        self._friend_name = choices.player_two
        self._ai_mode = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch()
        self.sheet = PaperSurface()
        self.sheet.setMaximumWidth(940)
        self.sheet.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.sheet_layout = QVBoxLayout(self.sheet)
        self.sheet_layout.setContentsMargins(32, 24, 32, 32)
        self.sheet_layout.setSpacing(16)
        heading_row = QHBoxLayout()
        self.back_button = button("Back", "quiet")
        self.back_button.clicked.connect(self.back_requested)
        heading_row.addWidget(self.back_button)
        heading_row.addWidget(label("Set the table", "heading"), 1)
        self.sheet_layout.addLayout(heading_row)

        columns = QHBoxLayout()
        columns.setSpacing(32)
        opponent = QVBoxLayout()
        opponent.setSpacing(10)
        opponent.addWidget(label("Choose an opponent", "fieldLabel"))
        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        self.mode_group = QButtonGroup(self)
        self.ai_button = button("Computer", checkable=True)
        self.pvp_button = button("A friend", checkable=True)
        for mode_id, choice in enumerate((self.ai_button, self.pvp_button)):
            self.mode_group.addButton(choice, mode_id)
            mode_row.addWidget(choice)
        opponent.addLayout(mode_row)
        self.difficulty_section = QWidget()
        difficulty_layout = QVBoxLayout(self.difficulty_section)
        difficulty_layout.setContentsMargins(0, 4, 0, 0)
        difficulty_layout.setSpacing(10)
        difficulty_layout.addWidget(label("Computer difficulty", "fieldLabel"))
        difficulty_row = QHBoxLayout()
        difficulty_row.setSpacing(8)
        self.difficulty_group = QButtonGroup(self)
        self.difficulty_buttons = {}
        for level_id, level in enumerate(("easy", "medium", "hard")):
            choice = button(level.title(), checkable=True)
            choice.setMinimumWidth(80)
            self.difficulty_group.addButton(choice, level_id)
            self.difficulty_buttons[level] = choice
            difficulty_row.addWidget(choice)
        difficulty_layout.addLayout(difficulty_row)
        self.difficulty_description = label("")
        self.difficulty_description.setMinimumHeight(40)
        difficulty_layout.addWidget(self.difficulty_description)
        opponent.addWidget(self.difficulty_section)
        self.local_description = label("Share the board and take turns on this computer.")
        opponent.addWidget(self.local_description)
        opponent.addStretch()
        columns.addLayout(opponent, 1)

        names = QVBoxLayout()
        names.setSpacing(10)
        self.player_one_label = label("Player 1", "blueLabel")
        self.player_one = QLineEdit(choices.player_one)
        self.player_one.setMaxLength(24)
        self.player_one.setAccessibleName("Player 1 name")
        self.player_one_label.setBuddy(self.player_one)
        self.player_two_label = label("Player 2", "coralLabel")
        self.player_two = QLineEdit(choices.player_two)
        self.player_two.setMaxLength(24)
        self.player_two.setAccessibleName("Player 2 name")
        self.player_one.returnPressed.connect(self.start_match)
        self.player_two.returnPressed.connect(self.start_match)
        self.player_two_label.setBuddy(self.player_two)
        for widget in (self.player_one_label, self.player_one, self.player_two_label, self.player_two):
            names.addWidget(widget)
        self.names_note = label("Names appear with your match.")
        names.addWidget(self.names_note)
        names.addStretch()
        columns.addLayout(names, 1)
        self.sheet_layout.addLayout(columns)

        footer = QHBoxLayout()
        self.error = label("", "error")
        self.error.setAccessibleName("Match setup message")
        footer.addWidget(self.error, 1)
        self.start_button = button("Start match", "primary")
        self.start_button.setMinimumWidth(180)
        self.start_button.clicked.connect(self.start_match)
        footer.addWidget(self.start_button)
        self.sheet_layout.addLayout(footer)
        outer.addWidget(self.sheet)
        outer.addStretch()

        self.mode_group.idClicked.connect(self._mode_changed)
        self.difficulty_group.idClicked.connect(self._difficulty_changed)
        self.difficulty_buttons[choices.difficulty].setChecked(True)
        self.ai_button.setChecked(choices.mode == "AI")
        self.pvp_button.setChecked(choices.mode == "PVP")
        self._mode_changed()
        self._difficulty_changed()

    def _mode_changed(self, *_):
        ai = self.ai_button.isChecked()
        if ai == self._ai_mode:
            return
        self._ai_mode = ai
        if ai and self.player_two.isEnabled():
            self._friend_name = self.player_two.text()
        self.player_two.setEnabled(not ai)
        self.player_two.setText("Computer" if ai else self._friend_name)
        self.player_two_label.setText("Opponent" if ai else "Player 2")
        self.player_one_label.setText("Your name" if ai else "Player 1")
        self.difficulty_section.setVisible(ai)
        self.local_description.setVisible(not ai)
        self.error.clear()

    def _difficulty_changed(self, *_):
        level = next(level for level, choice in self.difficulty_buttons.items() if choice.isChecked())
        descriptions = {
            "easy": "A relaxed opponent that picks random moves.",
            "medium": "Claims open boxes, then chooses randomly.",
            "hard": "Weighs captures, risks, and nearby edges.",
        }
        self.difficulty_description.setText(descriptions[level])

    def choices(self):
        return SetupChoices(
            "AI" if self.ai_button.isChecked() else "PVP",
            next(level for level, choice in self.difficulty_buttons.items() if choice.isChecked()),
            self.player_one.text().strip(),
            (self._friend_name.strip() or "Player 2") if self.ai_button.isChecked()
            else self.player_two.text().strip(),
        )

    def start_match(self):
        try:
            choices = self.choices()
        except ValueError:
            self.error.setText("Enter a name for each player to start.")
            (self.player_one if not self.player_one.text().strip() else self.player_two).setFocus()
            return
        saved = self.store.save(choices)
        self.error.setText("" if saved else "Your choices could not be saved for next time.")
        self.start_requested.emit(choices.match_config())

    def resizeEvent(self, event):
        compact = self.height() < 500
        self.sheet_layout.setContentsMargins(24 if compact else 32, 16 if compact else 24,
                                             24 if compact else 32, 36 if compact else 40)
        self.sheet_layout.setSpacing(8 if compact else 16)
        self.names_note.setVisible(not compact)
        super().resizeEvent(event)
