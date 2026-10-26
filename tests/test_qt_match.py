"""Verify the playable Paper Club screen through real Qt input and timers."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

from audio_support import quiet_audio
from core.game_engine import MatchConfig, Move
from test_game_engine import all_moves
from ui.qt_app import PaperClubWindow
from utils.setup_preferences import SetupStore


class QtMatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        if os.name == "nt" and "Segoe UI" not in QFontDatabase.families():
            QFontDatabase.addApplicationFont(str(
                Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "segoeui.ttf"))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = SetupStore(Path(self.temp.name) / "settings.json")
        self.store.save_reduced_motion(True)  # Immediate-state flow tests; timing is covered separately.
        self.window = PaperClubWindow(self.store, audio=quiet_audio(self.store))
        self.addCleanup(self.window.close)
        self.addCleanup(self.window.match.stop)
        self.window.resize(1180, 780)
        self.window.show()
        self.app.processEvents()
        self.match = self.window.match
        self.board = self.match.board

    def start(self, config=None):
        self.window.start_match(config or MatchConfig("PVP", None, ("Sam", "Robin")))
        self.app.processEvents()

    def click(self, move):
        QTest.mouseClick(self.board, Qt.MouseButton.LeftButton,
                         pos=self.board.edge_center(move).toPoint())

    def actions(self):
        return self.match.compact_actions if self.match.stage.compact else self.match.actions

    def test_mouse_preview_valid_move_and_invalid_margin_are_safe(self):
        self.start()
        edge = Move("row", (0, 0))
        QTest.mouseMove(self.board, self.board.edge_center(edge).toPoint())
        self.assertEqual(self.board.hovered, edge)
        self.assertEqual(self.match.engine.history, ())
        QTest.mouseClick(self.board, Qt.MouseButton.LeftButton, pos=QPoint(1, 1))
        self.assertEqual(self.match.engine.history, ())
        self.click(edge)
        self.assertEqual(self.match.engine.history[-1].move, edge)
        self.assertIsNone(self.board.hovered)
        self.assertIn("Robin", self.match.turn_banner.text())
        self.click(edge)
        self.assertEqual(len(self.match.engine.history), 1)

    def test_keyboard_can_select_both_directions_draw_and_leave_board(self):
        self.start()
        self.board.setFocus()
        QTest.keyClick(self.board, Qt.Key.Key_V)
        QTest.keyClick(self.board, Qt.Key.Key_Right)
        QTest.keyClick(self.board, Qt.Key.Key_Down)
        self.assertEqual(self.board.selected, Move("col", (1, 1)))
        self.assertIn("Vertical", self.board.accessibleName())
        QTest.keyClick(self.board, Qt.Key.Key_Return)
        self.assertEqual(self.match.engine.history[-1].move, Move("col", (1, 1)))
        QTest.keyClick(self.board, Qt.Key.Key_H)
        QTest.keyClick(self.board, Qt.Key.Key_Home)
        QTest.keyClick(self.board, Qt.Key.Key_Space)
        self.assertEqual(self.match.engine.history[-1].move, Move("row", (0, 0)))
        for _ in range(10):
            QTest.keyClick(self.board, Qt.Key.Key_Left)
            QTest.keyClick(self.board, Qt.Key.Key_Up)
        self.assertEqual(self.board.selected, Move("row", (0, 0)))
        QTest.keyClick(self.board, Qt.Key.Key_Tab)
        self.assertIsNot(self.window.focusWidget(), self.board)

    def test_hint_is_a_preview_and_undo_restores_the_turn(self):
        self.start()
        self.assertFalse(self.actions().undo.isEnabled())
        self.assertTrue(self.actions().undo.accessibleDescription())
        self.actions().hint.click()
        hint = self.board.hint
        self.assertIsNotNone(hint)
        self.assertTrue(self.match.engine.is_legal(hint))
        self.assertEqual(self.match.engine.history, ())
        QTest.keyClick(self.board, Qt.Key.Key_Return)
        self.assertEqual(self.match.engine.history[-1].move, hint)
        self.assertIsNone(self.board.hint)
        self.assertTrue(self.actions().undo.isEnabled())
        self.actions().undo.click()
        self.assertEqual(self.match.engine.history, ())
        self.assertIn("Sam", self.match.turn_banner.text())

    def test_capture_updates_scores_keeps_turn_and_disables_undo(self):
        self.start()
        for move in (Move("row", (0, 0)), Move("col", (0, 0)),
                     Move("row", (0, 1)), Move("col", (1, 0))):
            self.click(move)
        self.assertEqual(self.match.engine.scores, (0, 1))
        self.assertEqual(self.match.players[1].score.text(), "1")
        self.assertEqual(self.match.remaining.text(), "24 boxes left")
        self.assertIn("Robin", self.match.turn_banner.text())
        self.assertFalse(self.actions().undo.isEnabled())
        self.assertIn("cannot be undone", self.actions().undo.accessibleDescription())
        self.assertIn("+1", self.match.caption.text())

    def test_full_local_game_retains_completed_board_and_final_scores(self):
        self.start()
        for move in all_moves():
            self.click(move)
        self.assertTrue(self.match.engine.finished)
        self.assertFalse(self.match.controller.active)
        self.assertEqual(len(self.match.engine.history), 60)
        self.assertEqual(sum(self.match.engine.scores), 25)
        self.assertTrue((self.match.engine.box_owner != 0).all())
        self.assertEqual(sum(int(player.score.text()) for player in self.match.players), 25)
        self.assertEqual(self.match.remaining.text(), "0 boxes left")
        self.assertIn("wins", self.match.turn_banner.text())
        self.assertIs(self.window.pages.currentWidget(), self.match)
        self.assertFalse(self.board.input_enabled)
        self.assertFalse(self.actions().hint.isEnabled())
        self.assertFalse(self.actions().pause.isEnabled())
        self.match.home_button.click()
        self.assertIs(self.window.pages.currentWidget(), self.window.home)

    def test_ai_pause_cancels_timer_and_resume_plays_one_move(self):
        self.start(MatchConfig("AI", "medium", ("Sam", "Computer")))
        self.match.controller._ai_delay_ms = 10
        self.click(Move("row", (0, 0)))
        self.assertIn("thinking", self.match.turn_banner.text())
        self.assertFalse(self.actions().hint.isEnabled())
        self.assertEqual(len(self.match.timers), 1)
        self.actions().pause.click()
        self.assertTrue(self.match.controller.paused)
        self.assertTrue(self.board.paused)
        self.assertFalse(self.match.timers)
        QTest.keyClick(self.board, Qt.Key.Key_Return)
        self.click(Move("row", (1, 0)))
        QTest.qWait(30)
        self.assertEqual(len(self.match.engine.history), 1)
        with patch.object(self.match.engine.ai, "get_ai_move",
                          return_value=("row", (1, 0))) as choose:
            self.actions().pause.click()
            # Wait for the scheduled result; rendering the modal pause panel
            # can consume a fixed 40 ms wait on a busy or high-DPI desktop.
            for _ in range(100):
                if len(self.match.engine.history) == 2:
                    break
                QTest.qWait(10)
        choose.assert_called_once_with("medium")
        self.assertEqual(len(self.match.engine.history), 2)
        self.assertFalse(self.match.timers)
        self.assertTrue(self.actions().hint.isEnabled())
        self.assertFalse(self.actions().undo.isEnabled())

    def test_real_ai_difficulties_complete_through_qt_timers(self):
        # Import explicitly so an OS native-library block becomes a test error,
        # rather than an exception swallowed by a Qt signal callback.
        import numpy.random
        for difficulty in ("easy", "medium", "hard"):
            with self.subTest(difficulty=difficulty):
                self.start(MatchConfig("AI", difficulty, ("Sam", "Computer")))
                self.match.controller._ai_delay_ms = 0
                for _ in range(120):
                    if not self.match.controller.active:
                        break
                    if self.match.controller.accepts_human_move:
                        self.click(next(move for move in all_moves()
                                        if self.match.engine.is_legal(move)))
                    self.app.processEvents()
                self.assertTrue(self.match.engine.finished)
                self.assertEqual(len(self.match.engine.history), 60)
                self.assertEqual(sum(self.match.engine.scores), 25)
                self.assertFalse(self.match.timers)

    def test_native_ai_failure_preserves_match_and_pauses_with_retry(self):
        self.start(MatchConfig("AI", "medium", ("Sam", "Computer")))
        self.match.controller._ai_delay_ms = 0
        with patch.object(self.match.engine.ai, "get_ai_move", side_effect=ImportError("blocked DLL")):
            self.click(Move("row", (0, 0)))
            self.app.processEvents()
        self.assertEqual(len(self.match.engine.history), 1)
        self.assertTrue(self.match.controller.paused)
        self.assertFalse(self.match.timers)
        self.assertIn("unavailable", self.match.action_explanation.text())
        self.assertIn("retry", self.match.compact_explanation.text())
        with patch.object(self.match.engine.ai, "get_ai_move", return_value=("row", (1, 0))):
            self.actions().pause.click()
            self.app.processEvents()
        self.assertEqual(len(self.match.engine.history), 2)
        self.assertFalse(self.match.controller.paused)
        self.assertNotIn("unavailable", self.match.action_explanation.text())

    def test_cancel_navigation_preserves_match_and_discard_cancels_ai(self):
        self.start(MatchConfig("AI", "medium", ("Sam", "Computer")))
        self.match.controller._ai_delay_ms = 60000
        self.click(Move("row", (0, 0)))
        history = self.match.engine.history

        def cancel_dialog(*args):
            self.assertTrue(self.match.controller.paused)
            self.assertFalse(self.match.timers)
            return QMessageBox.StandardButton.Cancel

        with patch("ui.qt_app.QMessageBox.question", side_effect=cancel_dialog):
            self.window.show_home()
        self.assertIs(self.window.pages.currentWidget(), self.match)
        self.assertEqual(self.match.engine.history, history)
        self.assertFalse(self.match.controller.paused)
        self.assertEqual(len(self.match.timers), 1)
        self.match.controller.pause()
        with patch("ui.qt_app.QMessageBox.question", side_effect=cancel_dialog):
            self.window.show_setup()
        self.assertTrue(self.match.controller.paused)
        with patch("ui.qt_app.QMessageBox.question",
                   return_value=QMessageBox.StandardButton.Discard):
            self.window.show_home()
        self.assertIs(self.window.pages.currentWidget(), self.window.home)
        self.assertFalse(self.match.controller.active)
        self.assertFalse(self.match.timers)

    def test_minimizing_pauses_and_restoring_requires_explicit_resume(self):
        self.start(MatchConfig("AI", "medium", ("Sam", "Computer")))
        self.match.controller._ai_delay_ms = 60000
        self.click(Move("row", (0, 0)))
        self.window.showMinimized()
        self.app.processEvents()
        self.assertTrue(self.match.controller.paused)
        self.assertFalse(self.match.timers)
        self.window.showNormal()
        self.app.processEvents()
        self.assertTrue(self.match.controller.paused)
        self.actions().pause.click()
        self.assertFalse(self.match.controller.paused)
        self.assertEqual(len(self.match.timers), 1)

    def test_long_names_and_match_controls_fit_at_supported_sizes(self):
        self.start(MatchConfig("PVP", None, ("Alexandria Longlastname", "Christopher Longlastname")))
        for width, height in ((800, 480), (1047, 900), (1048, 740), (1048, 741),
                              (1049, 742), (1100, 760), (1366, 768), (1600, 900), (1920, 1080)):
            with self.subTest(width=width, height=height):
                self.window.resize(width, height)
                self.app.processEvents()
                self.assertEqual((self.window.width(), self.window.height()), (width, height))
                geometry, offset = self.board.board_geometry()
                self.assertGreaterEqual(geometry.size, 150)
                top_left = self.board.edge_center(Move("row", (0, 0)))
                top_right = self.board.edge_center(Move("row", (4, 0)))
                bottom_left = self.board.edge_center(Move("row", (0, 4)))
                self.assertAlmostEqual(top_right.x() - top_left.x(),
                                       bottom_left.y() - top_left.y())
                self.assertFalse(self.match.home_button.isVisible())
                self.assertFalse(self.match.compact_home.isVisible())
                controls = (self.actions().hint, self.actions().undo, self.actions().pause)
                for control in controls:
                    self.assertTrue(control.isVisible())
                    bounds = QRect(control.mapTo(self.window, QPoint()), control.size())
                    self.assertTrue(self.window.rect().contains(bounds), control.text())
                    self.assertGreaterEqual(control.height(), 44)
                self.assertEqual(self.match.players[0].avatar.size(),
                                 self.match.players[1].avatar.size())
                if self.match.stage.compact:
                    self.assertTrue(self.match.compact_strip.isVisible())
                    self.assertFalse(self.match.sidebar.isVisible())
                    self.assertFalse(self.match.compact_explanation.isVisible())
                    for index, player in enumerate(self.match.compact_players):
                        self.assertEqual(player.name.full_text,
                                         self.match.controller.config.player_names[index])
                        self.assertEqual(player.score.text(), "0")
                        bounds = QRect(player.score.mapTo(self.window, QPoint()), player.score.size())
                        self.assertTrue(self.window.rect().contains(bounds))
                else:
                    self.assertEqual(self.match.board_sheet.y(), self.match.sidebar.y())
                    self.assertEqual(self.match.board_sheet.height(), self.match.sidebar.height())
                    self.assertGreaterEqual(self.match.sidebar.height(),
                                            self.match.sidebar.minimumSizeHint().height())
                    for player in self.match.players:
                        for widget in (player.avatar, player.name, player.score):
                            bounds = QRect(widget.mapTo(self.match.sidebar, QPoint()), widget.size())
                            self.assertTrue(self.match.sidebar.rect().contains(bounds))

    def test_first_launch_is_fullscreen_and_windowed_preference_is_remembered(self):
        self.window.show_saved_window()
        self.app.processEvents()
        self.assertTrue(self.window.isFullScreen())
        self.assertTrue(self.window.fullscreen_action.isChecked())
        self.window.fullscreen_action.trigger()
        self.app.processEvents()
        self.assertFalse(self.window.isFullScreen())
        self.window.resize(1000, 700)
        self.app.processEvents()
        self.window.close()
        reopened = PaperClubWindow(self.store, audio=quiet_audio(self.store))
        self.addCleanup(reopened.close)
        reopened.show_saved_window()
        self.app.processEvents()
        self.assertFalse(reopened.isFullScreen())
        self.assertFalse(reopened.fullscreen_action.isChecked())
        self.assertEqual(self.store.load_window().width, 1000)
        self.assertEqual(self.store.load_window().height, 700)

    def test_escape_pauses_game_without_losing_match_or_leaving_fullscreen(self):
        self.start()
        self.window.set_fullscreen(True)
        self.app.processEvents()
        self.window.go_back()
        self.assertTrue(self.window.isFullScreen())
        self.assertTrue(self.match.controller.paused)
        self.assertIs(self.window.pages.currentWidget(), self.match)
        self.window.go_back()
        self.assertFalse(self.match.controller.paused)


if __name__ == "__main__":
    unittest.main()
