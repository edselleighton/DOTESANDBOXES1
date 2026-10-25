"""Verify navigation remains available after removing the global toolbar."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMenuBar, QMessageBox

from core.game_engine import MatchConfig, Move
from ui.qt_app import PaperClubWindow
from utils.setup_preferences import SetupStore
from test_game_engine import all_moves


class PaperNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        if os.name == "nt" and "Segoe UI" not in QFontDatabase.families():
            QFontDatabase.addApplicationFont("C:/Windows/Fonts/segoeui.ttf")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = SetupStore(Path(self.temp.name) / "settings.json")
        self.store.save_reduced_motion(True)
        self.window = PaperClubWindow(self.store)
        self.addCleanup(self.window.close)
        self.window.resize(1180, 780)
        self.window.show()
        self.app.processEvents()

    def test_home_routes_without_a_global_toolbar(self):
        self.assertFalse(any(menu.isVisible() for menu in self.window.findChildren(QMenuBar)))
        self.assertFalse(hasattr(self.window, "fullscreen_button"))
        self.window.home.instructions_button.click()
        self.assertIs(self.window.pages.currentWidget(), self.window.settings)
        self.assertEqual(self.window.settings.tabs.currentIndex(), 1)
        self.window.settings.done_button.click()
        self.assertIs(self.window.pages.currentWidget(), self.window.home)
        self.window.home.settings_button.click()
        self.assertEqual(self.window.settings.tabs.currentIndex(), 0)
        self.window.settings.done_button.click()
        self.window.play_button.click()
        self.assertIs(self.window.pages.currentWidget(), self.window.setup)

    def test_display_switches_and_f11_stay_in_sync_and_persist(self):
        self.window.show_settings()
        self.window.settings.reduced_motion.setChecked(False)
        self.assertFalse(self.window.motion.reduced_motion)
        self.assertFalse(self.window.reduced_motion_action.isChecked())
        self.assertFalse(self.store.load_reduced_motion())
        self.window.settings.fullscreen.setChecked(True)
        self.app.processEvents()
        self.assertTrue(self.window.isFullScreen())
        QTest.keyClick(self.window.settings.fullscreen, Qt.Key.Key_F11)
        self.app.processEvents()
        self.assertFalse(self.window.isFullScreen())
        self.assertFalse(self.window.settings.fullscreen.isChecked())

    def test_settings_during_ai_turn_preserves_and_requires_resume(self):
        self.window.start_match(MatchConfig("AI", "medium", ("Alex", "Computer")))
        match = self.window.match
        match.controller._ai_delay_ms = 60000
        match.play_human(Move("row", (0, 0)))
        history = match.engine.history
        self.assertEqual(len(match.timers), 1)
        self.window.show_settings()
        self.assertTrue(match.controller.paused)
        self.assertFalse(match.timers)
        self.window.settings.done_button.click()
        self.assertIs(self.window.pages.currentWidget(), match)
        self.assertTrue(self.window.pause_panel.isVisible())
        self.assertTrue(match.controller.paused)
        self.assertEqual(match.engine.history, history)
        self.window.pause_panel.resume.click()
        self.assertFalse(self.window.pause_panel.isVisible())
        self.assertFalse(match.controller.paused)
        self.assertEqual(len(match.timers), 1)
        self.assertEqual(match.engine.history, history)

    def test_pause_cancel_navigation_and_escape_are_safe(self):
        self.window.start_match(MatchConfig("PVP", None, ("Alex", "Casey")))
        match = self.window.match
        match.play_human(Move("row", (0, 0)))
        match.actions.pause.click()
        self.app.processEvents()
        self.assertTrue(self.window.pause_panel.isVisible())
        self.assertTrue(match.controller.paused)
        with patch("ui.qt_app.QMessageBox.question", return_value=QMessageBox.StandardButton.Cancel):
            self.window.pause_panel.home.click()
        self.assertIs(self.window.pages.currentWidget(), match)
        self.assertTrue(self.window.pause_panel.isVisible())
        self.assertTrue(match.controller.paused)
        QTest.keyClick(self.window.pause_panel, Qt.Key.Key_Escape)
        self.assertFalse(match.controller.paused)
        self.assertFalse(self.window.pause_panel.isVisible())
        self.assertEqual(len(match.engine.history), 1)

    def test_pause_keeps_keyboard_focus_inside_navigation(self):
        self.window.start_match(MatchConfig())
        self.window.match.toggle_pause()
        self.app.processEvents()
        panel = self.window.pause_panel
        panel.activateWindow()
        panel.resume.setFocus()
        self.app.processEvents()
        for _ in range(8):
            focused = self.app.focusWidget()
            self.assertTrue(focused is panel or panel.isAncestorOf(focused))
            QTest.keyClick(focused, Qt.Key.Key_Tab)
        self.assertTrue(self.window.match.controller.paused)

    def test_results_rematch_preserves_names_and_starts_a_clean_board(self):
        for width, height in ((800, 480), (1180, 780), (1000, 660)):
            self.window.resize(width, height)
            names = ("Alexandra Paper Champion", "Casey Stationery Captain")
            config = MatchConfig("PVP", None, names)
            self.window.start_match(config)
            self.app.processEvents()
            match = self.window.match
            for move in all_moves():
                match.play_human(move)
            self.app.processEvents()
            self.assertTrue(match.engine.finished)
            self.assertEqual(sum(match.engine.scores), 25)
            self.assertNotIn("Play again", match.caption.text())
            self.assertIn("Alex", match.result_names.text())
            self.assertIn("Casey", match.result_names.text())
            self.assertEqual(match.remaining.accessibleName(), "0 boxes remaining")
            controls = ((match.compact_rematch, match.compact_new, match.compact_result_home)
                        if match.stage.compact else (match.rematch_button, match.new_button, match.result_home))
            for control in controls:
                self.assertTrue(control.isVisible())
                bounds = QRect(control.mapTo(self.window, QPoint()), control.size())
                self.assertTrue(self.window.rect().contains(bounds))
            controls[0].click()
            self.assertEqual(match.controller.config, config)
            self.assertEqual(match.engine.scores, (0, 0))
            self.assertEqual(match.engine.history, ())
            self.assertTrue(match.controller.accepts_human_move)

    def test_panels_and_home_actions_fit_compact_and_wide_windows(self):
        for width, height in ((800, 480), (1180, 780), (1920, 1080)):
            self.window.resize(width, height)
            for tab in (0, 1):
                self.window.show_settings(tab)
                self.app.processEvents()
                controls = [self.window.settings.done_button, self.window.settings.exit_button]
                if tab == 0:
                    controls.extend([self.window.settings.fullscreen, self.window.settings.reduced_motion])
                for control in controls:
                    bounds = QRect(control.mapTo(self.window, QPoint()), control.size())
                    self.assertTrue(self.window.rect().contains(bounds), (width, height, control.accessibleName()))
                    self.assertGreaterEqual(control.height(), 44)
            self.window.close_settings()
            self.app.processEvents()
            for control in (self.window.home.play_button, self.window.home.instructions_button,
                            self.window.home.settings_button, self.window.home.scores_button):
                bounds = QRect(control.mapTo(self.window, QPoint()), control.size())
                self.assertTrue(self.window.rect().contains(bounds), (width, height, control.text()))
                self.assertGreaterEqual(control.height(), 44)
            self.assertFalse(self.window.home.scores_button.isEnabled())
            self.assertTrue(self.window.home.scores_button.accessibleDescription())


if __name__ == "__main__":
    unittest.main()
