"""Paper Club application shell, match navigation and window preferences."""

from PySide6.QtCore import QEvent, QSignalBlocker, QTimer
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QVBoxLayout,
)

from ui.match_page import MatchPage
from ui.audio import AudioManager
from ui.motion import MotionPolicy, PageStack, system_reduced_motion
from ui.motion_controls import MotionButton
from ui.paper_screens import SetupPage, WelcomePage
from ui.paper_panels import PausePanel, SettingsPage
from ui.paper_style import Tabletop, load_heading_font, stylesheet
from utils.setup_preferences import SetupStore, WindowPreferences


class PaperClubWindow(QMainWindow):
    def __init__(self, setup_store=None, *, audio=None):
        super().__init__()
        self.store = setup_store if setup_store is not None else SetupStore()
        self.window_preferences = self.store.load_window()
        self.motion = MotionPolicy(self.store.load_reduced_motion(system_reduced_motion()), self)
        self.setWindowTitle("Dots and Boxes — Paper Club")
        self.setMinimumSize(800, 480)
        self.resize(self.window_preferences.width, self.window_preferences.height)
        self._was_maximized = False
        self.setStyleSheet(stylesheet(load_heading_font()))
        self.tabletop = Tabletop()
        self.setCentralWidget(self.tabletop)
        self.table_layout = QVBoxLayout(self.tabletop)
        self.table_layout.setContentsMargins(24, 24, 24, 24)
        self.table_layout.setSpacing(0)

        self.pages = PageStack(self.motion)
        self.home = WelcomePage()
        self.setup = SetupPage(self.store)
        self.settings = SettingsPage()
        self.match = MatchPage()
        self.match.set_motion_policy(self.motion)
        self.pages.addWidget(self.home)
        self.pages.addWidget(self.setup)
        self.pages.addWidget(self.match)
        self.pages.addWidget(self.settings)
        self._settings_return = self.home
        self.pause_panel = PausePanel(self)
        self.table_layout.addWidget(self.pages, 1)
        self.play_button = self.home.play_button
        self.home.play_requested.connect(self.show_setup)
        self.home.settings_requested.connect(self.show_settings)
        self.home.instructions_requested.connect(lambda: self.show_settings(1))
        self.settings.done_requested.connect(self.close_settings)
        self.settings.exit_requested.connect(self.close)
        self.settings.fullscreen_changed.connect(self.set_fullscreen)
        self.settings.reduced_motion_changed.connect(self.set_reduced_motion)
        self.settings.stronger_contrast_changed.connect(self.set_stronger_contrast)
        self.settings.audio_changed.connect(self.set_audio_preferences)
        self.setup.back_requested.connect(self.show_home)
        self.setup.start_requested.connect(self.start_match)
        self.match.home_requested.connect(self.show_home)
        self.match.new_match_requested.connect(self.show_setup)
        self.match.pause_requested.connect(self.show_pause_panel)
        self.pause_panel.resume_requested.connect(self.resume_match)
        self.pause_panel.settings_requested.connect(self.show_settings)
        self.pause_panel.new_requested.connect(lambda: self.navigate_from_pause(self.show_setup))
        self.pause_panel.home_requested.connect(lambda: self.navigate_from_pause(self.show_home))
        for actions in (self.match.actions, self.match.compact_actions):
            actions.pause.clicked.connect(self.sync_pause_panel)

        self.fullscreen_action = QAction("Fullscreen", self)
        self.fullscreen_action.setCheckable(True)
        self.fullscreen_action.setShortcut(QKeySequence("F11"))
        self.fullscreen_action.toggled.connect(self.set_fullscreen)
        self.addAction(self.fullscreen_action)
        self.reduced_motion_action = QAction("Reduced motion", self)
        self.reduced_motion_action.setCheckable(True)
        self.reduced_motion_action.setChecked(self.motion.reduced_motion)
        self.reduced_motion_action.toggled.connect(self.set_reduced_motion)
        self.addAction(self.reduced_motion_action)
        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.activated.connect(self.go_back)
        self.audio = audio if audio is not None else AudioManager(self.store.load_audio(), self)
        self.settings.set_audio_preferences(self.audio.preferences)
        self.audio.status_changed.connect(self.update_audio_status)
        self.settings.sample_requested.connect(lambda: self.audio.play("capture"))
        self.match.sound_requested.connect(self.audio.play)
        self._audio_save_timer = QTimer(self)
        self._audio_save_timer.setSingleShot(True)
        self._audio_save_timer.timeout.connect(self.save_audio_preferences)
        self._audio_warning = ""
        self.update_audio_status()
        contrast = self.store.load_stronger_contrast()
        with QSignalBlocker(self.settings.stronger_contrast):
            self.settings.stronger_contrast.setChecked(contrast)
        self.match.board.set_stronger_contrast(contrast)
        for control in self.findChildren(MotionButton):
            control.set_motion_policy(self.motion)
            if control is not self.settings.sample_button:
                control.clicked.connect(lambda checked=False: self.audio.play("menu"))

    def set_audio_preferences(self, preferences):
        self.audio.set_preferences(preferences)
        # Keep dragging responsive; write the final choice atomically after a
        # short quiet period, and flush before leaving Settings or closing.
        self._audio_save_timer.start(250)

    def save_audio_preferences(self):
        self._audio_save_timer.stop()
        saved = self.store.save_audio(self.audio.preferences)
        self._audio_warning = "" if saved else "Sound changed for this session; preferences could not be saved."
        self.update_audio_status()

    def update_audio_status(self, *_):
        self.settings.set_audio_status(" ".join(text for text in
                                               (self._audio_warning, self.audio.message) if text))

    def set_stronger_contrast(self, enabled):
        self.match.board.set_stronger_contrast(enabled)
        with QSignalBlocker(self.settings.stronger_contrast):
            self.settings.stronger_contrast.setChecked(enabled)
        if not self.store.save_stronger_contrast(enabled):
            self.statusBar().showMessage("Board contrast changed for this session; preferences could not be saved.", 5000)

    def set_reduced_motion(self, enabled):
        self.motion.set_reduced_motion(enabled)
        with QSignalBlocker(self.reduced_motion_action), QSignalBlocker(self.settings.reduced_motion):
            self.reduced_motion_action.setChecked(enabled)
            self.settings.reduced_motion.setChecked(enabled)
        if not self.store.save_reduced_motion(enabled):
            self.statusBar().showMessage("Reduced motion changed for this session; preferences could not be saved.", 5000)

    def show_settings(self, tab=0):
        if self.pages.currentWidget() is not self.settings:
            self._settings_return = self.pages.currentWidget()
        if self._settings_return is self.match:
            self.match.controller.pause()
        self.pause_panel.hide()
        with QSignalBlocker(self.settings.fullscreen), QSignalBlocker(self.settings.reduced_motion):
            self.settings.fullscreen.setChecked(self.isFullScreen())
            self.settings.reduced_motion.setChecked(self.motion.reduced_motion)
        self.settings.tabs.setCurrentIndex(tab)
        self.settings.set_audio_preferences(self.audio.preferences)
        self.pages.setCurrentWidget(self.settings)
        self.settings.tabs.setFocus()

    def close_settings(self):
        if self._audio_save_timer.isActive():
            self.save_audio_preferences()
        self.pages.setCurrentWidget(self._settings_return)
        if self._settings_return is self.match and self.match.controller.active:
            self.show_pause_panel()
        elif self._settings_return is self.home:
            self.home.settings_button.setFocus()

    def show_pause_panel(self):
        if self.pages.currentWidget() is self.match and self.match.controller.active:
            self.pause_panel.explanation.setText(self.match._ai_error or "Your board is right where you left it.")
            self.pause_panel.show()
            self.pause_panel.raise_()

    def resume_match(self):
        self.pause_panel.hide()
        if self.match.controller.paused:
            self.match.toggle_pause()

    def sync_pause_panel(self):
        if not self.match.controller.paused:
            self.pause_panel.hide()

    def navigate_from_pause(self, navigate):
        self.pause_panel.hide()
        navigate()
        if self.pages.currentWidget() is self.match and self.match.controller.paused:
            self.show_pause_panel()

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
        self.pause_panel.hide()
        self.pages.setCurrentWidget(self.setup)
        self.setup.mode_group.checkedButton().setFocus()

    def show_home(self):
        if not self._can_leave_match():
            return
        self.pause_panel.hide()
        self.pages.setCurrentWidget(self.home)
        self.play_button.setFocus()

    def start_match(self, config):
        self.pause_panel.hide()
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
        with QSignalBlocker(self.fullscreen_action), QSignalBlocker(self.settings.fullscreen):
            self.fullscreen_action.setChecked(enabled)
            self.settings.fullscreen.setChecked(enabled)

    def leave_fullscreen(self):
        if self.isFullScreen():
            self.fullscreen_action.setChecked(False)

    def go_back(self):
        if self.pause_panel.isVisible():
            self.resume_match()
        elif self.pages.currentWidget() is self.settings:
            self.close_settings()
        elif self.pages.currentWidget() is self.match and self.match.controller.active:
            self.match.toggle_pause()
        elif self.isFullScreen():
            self.leave_fullscreen()
        elif self.pages.currentWidget() is self.setup:
            self.show_home()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange and hasattr(self, "match"):
            if self.isMinimized():
                self.match.controller.pause()
            self.motion.set_suspended(self.isMinimized())
            if hasattr(self, "audio"):
                self.audio.set_suspended(self.isMinimized())
            enabled = self.isFullScreen()
            with QSignalBlocker(self.fullscreen_action), QSignalBlocker(self.settings.fullscreen):
                self.fullscreen_action.setChecked(enabled)
                self.settings.fullscreen.setChecked(enabled)
        super().changeEvent(event)

    def closeEvent(self, event):
        if self._audio_save_timer.isActive():
            self.save_audio_preferences()
        self.audio.close()
        self.pause_panel.hide()
        self.motion.set_suspended(True)
        self.match.stop()
        size = self.normalGeometry().size()
        self.store.save_window(WindowPreferences(
            fullscreen=self.isFullScreen(),
            maximized=self._was_maximized if self.isFullScreen() else self.isMaximized(),
            width=max(800, min(16384, size.width())),
            height=max(480, min(16384, size.height())),
        ))
        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.audio.start()

    def resizeEvent(self, event):
        compact = self.width() < 1000 or self.height() < 620
        margin = 12 if compact else 24
        self.table_layout.setContentsMargins(margin, margin, margin, margin)
        super().resizeEvent(event)


def run():
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("Dots and Boxes")
    app.setOrganizationName("Paper Club")
    window = PaperClubWindow()
    window.show_saved_window()
    return app.exec()
