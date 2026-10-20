"""Paper Club application shell and the match-setup handoff."""

import sys
from pathlib import Path

from PySide6.QtCore import QProcess
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QStackedWidget, QVBoxLayout

from ui.paper_screens import SetupPage, WelcomePage
from ui.paper_style import Tabletop, button, label, load_heading_font, stylesheet
from utils.setup_preferences import SetupStore


def classic_command(config=None):
    arguments = [] if getattr(sys, "frozen", False) else [
        str(Path(__file__).resolve().parents[1] / "main.py")
    ]
    if config is not None:
        arguments.extend(("--mode", config.mode, "--player-one", config.player_names[0],
                          "--player-two", config.player_names[1]))
        if config.mode == "AI":
            arguments.extend(("--difficulty", config.difficulty))
    return sys.executable, arguments


class PaperClubWindow(QMainWindow):
    def __init__(self, setup_store=None):
        super().__init__()
        self.setWindowTitle("Dots and Boxes — Paper Club")
        self.setMinimumSize(800, 480)
        self.resize(1180, 780)
        self._was_maximized = False
        self.setStyleSheet(stylesheet(load_heading_font()))
        self.tabletop = Tabletop()
        self.setCentralWidget(self.tabletop)
        self.table_layout = QVBoxLayout(self.tabletop)
        self.table_layout.setContentsMargins(24, 16, 24, 24)
        self.table_layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(label("Paper Club", "brand"))
        header.addStretch()
        self.fullscreen_button = button("Fullscreen", "quiet")
        header.addWidget(self.fullscreen_button)
        exit_button = button("Exit", "quiet")
        exit_button.clicked.connect(self.close)
        header.addWidget(exit_button)
        self.table_layout.addLayout(header)

        self.pages = QStackedWidget()
        self.home = WelcomePage()
        self.setup = SetupPage(setup_store if setup_store is not None else SetupStore())
        self.pages.addWidget(self.home)
        self.pages.addWidget(self.setup)
        self.table_layout.addWidget(self.pages, 1)
        self.play_button = self.home.play_button
        self.home.play_requested.connect(self.show_setup)
        self.setup.back_requested.connect(self.show_home)
        self.setup.start_requested.connect(self.start_match)

        game_menu = self.menuBar().addMenu("Game")
        game_menu.addAction("New match", self.show_setup)
        game_menu.addAction("Home", self.show_home)
        game_menu.addSeparator()
        game_menu.addAction("Exit", self.close)
        view_menu = self.menuBar().addMenu("View")
        self.fullscreen_action = QAction("Fullscreen", self)
        self.fullscreen_action.setCheckable(True)
        self.fullscreen_action.setShortcut(QKeySequence("F11"))
        self.fullscreen_action.toggled.connect(self.set_fullscreen)
        view_menu.addAction(self.fullscreen_action)
        self.fullscreen_button.clicked.connect(self.fullscreen_action.trigger)
        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.activated.connect(self.go_back)

    def show_setup(self):
        self.pages.setCurrentWidget(self.setup)
        self.setup.mode_group.checkedButton().setFocus()

    def show_home(self):
        self.pages.setCurrentWidget(self.home)
        self.play_button.setFocus()

    def start_match(self, config):
        program, arguments = classic_command(config)
        started, _ = QProcess.startDetached(program, arguments)
        if not started:
            self.setup.error.setText("The game could not open. Please try again.")

    def set_fullscreen(self, enabled):
        if enabled:
            self._was_maximized = self.isMaximized()
            self.showFullScreen()
        elif self._was_maximized:
            self.showMaximized()
        else:
            self.showNormal()
        self.fullscreen_button.setText("Windowed" if enabled else "Fullscreen")

    def leave_fullscreen(self):
        if self.isFullScreen():
            self.fullscreen_action.setChecked(False)

    def go_back(self):
        if self.isFullScreen():
            self.leave_fullscreen()
        elif self.pages.currentWidget() is self.setup:
            self.show_home()

    def resizeEvent(self, event):
        compact = self.width() < 1000 or self.height() < 620
        self.table_layout.setContentsMargins(16 if compact else 24, 12 if compact else 16,
                                             16 if compact else 24, 16 if compact else 24)
        super().resizeEvent(event)


def run():
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("Dots and Boxes")
    app.setOrganizationName("Paper Club")
    window = PaperClubWindow()
    window.showMaximized()
    return app.exec()
