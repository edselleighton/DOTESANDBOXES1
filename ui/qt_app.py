"""Qt application shell. Match screens are migrated in subsequent increments."""

import sys
from pathlib import Path

from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QLabel, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)


def classic_command():
    if getattr(sys, "frozen", False):
        return sys.executable, []
    return sys.executable, [str(Path(__file__).resolve().parents[1] / "main.py")]


class PaperClubWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dots and Boxes — Paper Club")
        self.setMinimumSize(800, 480)
        self.resize(1100, 760)
        self._was_maximized = False
        self.pages = QStackedWidget(self)
        self.setCentralWidget(self.pages)
        home = QWidget()
        layout = QVBoxLayout(home)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        layout.addStretch()
        edition = QLabel("PAPER CLUB")
        edition.setObjectName("edition")
        title = QLabel("Dots & Boxes")
        title.setObjectName("wordmark")
        subtitle = QLabel("One line can change the game.")
        subtitle.setWordWrap(True)
        for label in (edition, title, subtitle):
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        self.play_button = QPushButton("Play")
        self.play_button.setMinimumSize(200, 48)
        self.play_button.setAccessibleDescription("Open a Dots and Boxes game")
        self.play_button.clicked.connect(self.open_game)
        layout.addSpacing(16)
        layout.addWidget(self.play_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        self.pages.addWidget(home)

        game_menu = self.menuBar().addMenu("Game")
        game_menu.addAction("Play", self.open_game)
        game_menu.addSeparator()
        game_menu.addAction("Exit", self.close)
        view_menu = self.menuBar().addMenu("View")
        self.fullscreen_action = QAction("Fullscreen", self)
        self.fullscreen_action.setCheckable(True)
        self.fullscreen_action.setShortcut(QKeySequence("F11"))
        self.fullscreen_action.toggled.connect(self.set_fullscreen)
        view_menu.addAction(self.fullscreen_action)
        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.activated.connect(self.leave_fullscreen)

        self.setStyleSheet("""
            QMainWindow, QStackedWidget, QWidget { background: #F2EBDD; color: #203B35; }
            QLabel { font-family: 'Segoe UI'; font-size: 16px; }
            QLabel#edition { color: #53694F; font-size: 14px; letter-spacing: 3px; }
            QLabel#wordmark { font-size: 40px; font-weight: 700; }
            QPushButton { background: #576F50; color: #FFFFFF; border: 2px solid #576F50;
                          border-radius: 8px; padding: 10px 24px; font-size: 18px; }
            QPushButton:hover { background: #445C3E; }
            QPushButton:focus { border: 2px solid #203B35; }
            QMenuBar, QMenu { font-family: 'Segoe UI'; font-size: 14px; }
            QMenuBar::item:selected, QMenu::item:selected { background: #D5DEC9; }
        """)

    def open_game(self):
        program, arguments = classic_command()
        started, _ = QProcess.startDetached(program, arguments)
        if not started:
            QMessageBox.warning(self, "Unable to open game", "Please try opening the game again.")

    def set_fullscreen(self, enabled):
        if enabled:
            self._was_maximized = self.isMaximized()
            self.showFullScreen()
        elif self._was_maximized:
            self.showMaximized()
        else:
            self.showNormal()

    def leave_fullscreen(self):
        if self.isFullScreen():
            self.fullscreen_action.setChecked(False)


def run():
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("Dots and Boxes")
    app.setOrganizationName("Paper Club")
    window = PaperClubWindow()
    window.showMaximized()
    return app.exec()
