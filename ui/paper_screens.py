"""Paper Club welcome and match setup screens."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLineEdit, QSizePolicy, QVBoxLayout, QWidget,
)

from ui.paper_style import BoardIllustration, PaperSurface, button, label
from utils.setup_preferences import SetupChoices


class WelcomePage(QWidget):
    play_requested = Signal()

    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch()
        self.sheet = PaperSurface()
        self.sheet.setMaximumWidth(1120)
        content = QHBoxLayout(self.sheet)
        content.setContentsMargins(48, 40, 36, 48)
        content.setSpacing(24)
        self.copy = QWidget()
        copy_layout = QVBoxLayout(self.copy)
        copy_layout.setContentsMargins(0, 0, 0, 0)
        copy_layout.setSpacing(16)
        copy_layout.addWidget(label("A LITTLE TABLETOP STRATEGY", "eyebrow"))
        self.title = label('<span style="color:#265A80">Dots <span style="color:#57704F">&amp;</span></span>'
                           '<br><span style="color:#CB513C">Boxes</span>', "homeTitle")
        self.title.setWordWrap(False)
        self.title.setAccessibleName("Dots and Boxes")
        copy_layout.addWidget(self.title)
        copy_layout.addWidget(label("One line can change the game.", "lead"))
        self.description = label("Complete a box to score—and take another turn.")
        self.description.setMaximumWidth(330)
        copy_layout.addWidget(self.description)
        copy_layout.addSpacing(8)
        self.play_button = button("Play a round", "primary")
        self.play_button.setMinimumWidth(230)
        self.play_button.setAccessibleDescription("Choose an opponent and set up a match")
        self.play_button.clicked.connect(self.play_requested)
        copy_layout.addWidget(self.play_button, alignment=Qt.AlignmentFlag.AlignLeft)
        copy_layout.addWidget(label("Two players · Three AI levels"))
        content.addWidget(self.copy, 1)
        self.illustration = BoardIllustration()
        content.addWidget(self.illustration, 1)
        outer.addWidget(self.sheet, alignment=Qt.AlignmentFlag.AlignHCenter)
        outer.addStretch()
        self._content_layout = content
        self._compact = None

    def resizeEvent(self, event):
        compact = self.width() < 900 or self.height() < 560
        self.illustration.setVisible(not compact)
        self.description.setVisible(self.height() >= 400)
        self._content_layout.setContentsMargins(32 if compact else 48, 24 if compact else 40,
                                               32 if compact else 36, 32 if compact else 48)
        if compact != self._compact:
            self._compact = compact
            self.title.setStyleSheet(f"font-size: {52 if compact else 72}px;")
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
