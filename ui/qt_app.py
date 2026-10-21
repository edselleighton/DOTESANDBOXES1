"""Paper Club application shell, match navigation and window preferences."""

from PySide6.QtCore import QEvent, QSignalBlocker
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QMainWindow, QMessageBox, QStackedWidget, QVBoxLayout,
)

from ui.match_page import MatchPage
from ui.paper_screens import SetupPage, WelcomePage
from ui.paper_style import Tabletop, button, label, load_heading_font, stylesheet
from utils.setup_preferences import SetupStore, WindowPreferences


class PaperClubWindow(QMainWindow):
    def __init__(self, setup_store=None):
        super().__init__()
        self.store = setup_store if setup_store is not None else SetupStore()
        self.window_preferences = self.store.load_window()
        self.setWindowTitle("Dots and Boxes — Paper Club")
        self.setMinimumSize(800, 480)
        self.resize(self.window_preferences.width, self.window_preferences.height)
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
        self.setup = SetupPage(self.store)
        self.match = MatchPage()
        self.pages.addWidget(self.home)
        self.pages.addWidget(self.setup)
        self.pages.addWidget(self.match)
        self.table_layout.addWidget(self.pages, 1)
        self.play_button = self.home.play_button
        self.home.play_requested.connect(self.show_setup)
        self.setup.back_requested.connect(self.show_home)
        self.setup.start_requested.connect(self.start_match)
        self.match.home_requested.connect(self.show_home)
        self.match.new_match_requested.connect(self.show_setup)

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

    def show_saved_window(self):
        preferences = self.window_preferences
        screen = self.screen().availableGeometry()
        self.resize(max(800, min(preferences.width, screen.width())),
                    max(480, min(preferences.height, screen.height())))
        if preferences.fullscreen:
            self.set_fullscreen(True)
            self._was_maximized = preferences.maximized
        elif preferences.maximized:
            self.showMaximized()
        else:
            self.show()

    def _can_leave_match(self):
        controller = self.match.controller
        if self.pages.currentWidget() is not self.match or not controller.active:
            return True
        was_paused = controller.paused
        controller.pause()
        answer = QMessageBox.question(
            self, "Leave this match?", "Return to the menu? Your current match will be lost.",
            QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Discard:
            self.match.stop()
            return True
        if not was_paused:
            controller.resume()
        return False

    def show_setup(self):
        if not self._can_leave_match():
            return
        self.pages.setCurrentWidget(self.setup)
        self.setup.mode_group.checkedButton().setFocus()

    def show_home(self):
        if not self._can_leave_match():
            return
        self.pages.setCurrentWidget(self.home)
        self.play_button.setFocus()

    def start_match(self, config):
        self.pages.setCurrentWidget(self.match)
        self.match.start(config)

    def set_fullscreen(self, enabled):
        if enabled:
            self._was_maximized = self.isMaximized()
            self.showFullScreen()
        elif self._was_maximized:
            self.showMaximized()
        else:
            self.showNormal()
        self.fullscreen_button.setText("Windowed" if enabled else "Fullscreen")
        with QSignalBlocker(self.fullscreen_action):
            self.fullscreen_action.setChecked(enabled)

    def leave_fullscreen(self):
        if self.isFullScreen():
            self.fullscreen_action.setChecked(False)

    def go_back(self):
        if self.pages.currentWidget() is self.match and self.match.controller.active:
            self.match.toggle_pause()
        elif self.isFullScreen():
            self.leave_fullscreen()
        elif self.pages.currentWidget() is self.setup:
            self.show_home()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange and hasattr(self, "match"):
            if self.isMinimized():
                self.match.controller.pause()
            enabled = self.isFullScreen()
            with QSignalBlocker(self.fullscreen_action):
                self.fullscreen_action.setChecked(enabled)
            self.fullscreen_button.setText("Windowed" if enabled else "Fullscreen")
        super().changeEvent(event)

    def closeEvent(self, event):
        self.match.stop()
        size = self.normalGeometry().size()
        self.store.save_window(WindowPreferences(
            fullscreen=self.isFullScreen(),
            maximized=self._was_maximized if self.isFullScreen() else self.isMaximized(),
            width=max(800, min(16384, size.width())),
            height=max(480, min(16384, size.height())),
        ))
        super().closeEvent(event)

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
    window.show_saved_window()
    return app.exec()
