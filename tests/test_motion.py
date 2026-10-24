"""Exercise motion through actual widgets while keeping game state immediate."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QAbstractAnimation, Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

from core.game_engine import MatchConfig, Move
from ui.motion import CAPTURE_MS, LINE_MS, PAGE_MS
from ui.motion_controls import MotionButton
from ui.qt_app import PaperClubWindow
from utils.setup_preferences import SetupStore
from test_game_engine import all_moves


class MatchMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        if os.name == "nt" and "Segoe UI" not in QFontDatabase.families():
            QFontDatabase.addApplicationFont("C:/Windows/Fonts/segoeui.ttf")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = SetupStore(Path(self.temp.name) / "settings.json")
        self.store.save_reduced_motion(False)
        self.window = PaperClubWindow(self.store)
        self.addCleanup(self.window.close)
        self.window.show()
        self.window.start_match(MatchConfig("PVP", None, ("Sam", "Robin")))
        self.window.pages.finish_transition()
        self.app.processEvents()
        self.match = self.window.match
        self.board = self.match.board

    def click(self, move):
        QTest.mouseClick(self.board, Qt.MouseButton.LeftButton,
                         pos=self.board.edge_center(move).toPoint())

    def finish(self):
        self.board.animation.setCurrentTime(self.board.animation.duration())

    def test_line_feedback_blocks_duplicate_input_then_releases_controls(self):
        self.click(Move("row", (0, 0)))
        self.assertEqual(len(self.match.engine.history), 1)
        self.assertTrue(self.board.animating)
        self.assertEqual(self.board.animation.duration(), LINE_MS)
        self.assertFalse(self.board.input_enabled)
        self.assertFalse(self.match.actions.hint.isEnabled())
        self.assertFalse(self.match.actions.undo.isEnabled())
        self.click(Move("row", (1, 0)))
        QTest.keyClick(self.board, Qt.Key.Key_Space)
        self.match.undo()
        self.match.show_hint()
        self.assertEqual(len(self.match.engine.history), 1)
        self.assertIsNone(self.board.hint)
        self.finish()
        self.assertTrue(self.board.input_enabled)
        self.assertTrue(self.match.actions.undo.isEnabled())
        self.click(Move("row", (1, 0)))
        self.assertEqual(len(self.match.engine.history), 2)

    def test_captured_box_scores_immediately_while_fill_is_animating(self):
        for move in (Move("row", (0, 0)), Move("col", (0, 0)), Move("row", (0, 1))):
            self.click(move)
            self.finish()
        self.click(Move("col", (1, 0)))
        self.assertEqual(self.match.engine.scores, (0, 1))
        self.assertEqual(self.match.players[1].score.text(), "1")
        self.assertEqual(self.match.remaining.text(), "24 boxes left")
        self.assertEqual(self.board.animation.duration(), CAPTURE_MS)
        self.assertEqual(self.board.feedback.captured_boxes, ((0, 0),))
        self.board.animation.pause()
        self.board.animation.setCurrentTime(0)
        geometry, offset = self.board.board_geometry()
        point = offset + self.board.edge_center(Move("row", (0, 0))) - offset
        # Sample inside the newly owned box, away from its letter and edges.
        point.setX(offset.x() + geometry.spacing * .7)
        point.setY(offset.y() + geometry.spacing * .7)

        def sample():
            image = self.board.grab().toImage()
            ratio = image.devicePixelRatio()
            return image.pixelColor(round(point.x() * ratio), round(point.y() * ratio))

        initial = sample()
        self.board.animation.setCurrentTime(CAPTURE_MS // 2)
        middle = sample()
        self.board.finish_feedback()
        final = sample()
        self.assertNotEqual(initial, middle)
        self.assertNotEqual(middle, final)
        self.assertEqual(self.match.engine.scores, (0, 1))
        self.assertFalse(self.match.actions.undo.isEnabled())
        self.assertTrue(self.board.input_enabled)

    def test_reduced_motion_settles_current_effect_and_persists(self):
        self.click(Move("row", (0, 0)))
        self.window.reduced_motion_action.setChecked(True)
        self.assertFalse(self.board.animating)
        self.assertTrue(self.board.input_enabled)
        self.assertTrue(self.store.load_reduced_motion())
        self.click(Move("row", (1, 0)))
        self.assertFalse(self.board.animating)
        self.assertEqual(len(self.match.engine.history), 2)
        reopened = PaperClubWindow(self.store)
        self.addCleanup(reopened.close)
        self.assertTrue(reopened.reduced_motion_action.isChecked())

    def test_pause_and_minimize_stop_motion_without_changing_moves(self):
        self.click(Move("row", (0, 0)))
        self.match.toggle_pause()
        self.assertFalse(self.board.animating)
        self.assertFalse(self.board.input_enabled)
        self.match.toggle_pause()
        self.click(Move("row", (1, 0)))
        self.window.showMinimized()
        self.app.processEvents()
        self.assertTrue(self.match.controller.paused)
        self.assertFalse(self.board.animating)
        self.assertFalse(self.window.motion.enabled)
        for control in self.window.findChildren(MotionButton):
            self.assertEqual(control.animation.state(), QAbstractAnimation.State.Stopped)
        self.window.showNormal()
        self.app.processEvents()
        self.assertTrue(self.match.controller.paused)
        self.assertTrue(self.window.motion.enabled)
        self.assertEqual(len(self.match.engine.history), 2)

    def test_leaving_and_restart_do_not_replay_old_effects(self):
        self.click(Move("row", (0, 0)))
        with patch("ui.qt_app.QMessageBox.question", return_value=QMessageBox.StandardButton.Discard):
            self.window.show_home()
        self.assertFalse(self.board.animating)
        self.window.start_match(MatchConfig())
        QTest.qWait(CAPTURE_MS + 40)
        self.assertEqual(self.match.engine.history, ())
        self.assertIsNone(self.board.feedback)
        self.assertTrue(self.board.input_enabled)

    def test_screen_transition_interruptions_resize_and_hide_cleanup(self):
        self.window.start_match(MatchConfig())
        with patch("ui.qt_app.QMessageBox.question", return_value=QMessageBox.StandardButton.Discard):
            self.window.show_home()
        self.window.show_setup()
        self.assertIsNone(self.window.home.graphicsEffect())
        self.assertIsNotNone(self.window.setup.graphicsEffect())
        self.assertEqual(self.window.pages.animation.duration(), PAGE_MS)
        self.window.resize(1100, 760)
        self.app.processEvents()
        self.assertIsNone(self.window.setup.graphicsEffect())
        self.window.show_home()
        self.window.hide()
        self.assertEqual(self.window.pages.animation.state(), QAbstractAnimation.State.Stopped)
        self.assertIsNone(self.window.home.graphicsEffect())

    def test_reduced_motion_removes_transition_without_disabling_navigation(self):
        self.window.motion.set_reduced_motion(True)
        with patch("ui.qt_app.QMessageBox.question", return_value=QMessageBox.StandardButton.Discard):
            self.window.show_home()
        self.window.play_button.click()
        self.assertIs(self.window.pages.currentWidget(), self.window.setup)
        self.assertIsNone(self.window.setup.graphicsEffect())
        self.assertEqual(self.window.pages.animation.state(), QAbstractAnimation.State.Stopped)

    def test_consecutive_computer_captures_have_separate_delays_and_effects(self):
        self.window.start_match(MatchConfig("AI", "medium"))
        self.window.pages.finish_transition()
        for move in (Move("row", (0, 0)), Move("row", (0, 1)), Move("col", (0, 0)),
                     Move("row", (3, 3)), Move("row", (3, 4)), Move("col", (3, 3))):
            self.match.engine.play(move)
        self.match._on_move(None)
        self.click(Move("row", (4, 5)))
        self.finish()
        with patch.object(self.match.engine.ai, "get_ai_move",
                          side_effect=[("col", (1, 0)), ("col", (4, 3))]):
            for expected_score in (1, 2):
                self.assertEqual(len(self.match.timers), 1)
                timer = next(iter(self.match.timers))
                self.assertGreaterEqual(timer.interval(), CAPTURE_MS + 40)
                timer.stop()
                timer.timeout.emit()
                self.assertEqual(self.match.engine.scores[1], expected_score)
                self.assertTrue(self.board.animating)
                self.assertEqual(len(self.match.timers), 1)
                self.assertFalse(self.board.input_enabled)
                self.finish()
        self.match.toggle_pause()
        self.assertFalse(self.match.timers)

    def test_complete_animated_game_keeps_final_score_and_board(self):
        for move in all_moves():
            self.click(move)
            if self.match.engine.finished:
                break
            self.finish()
        self.assertTrue(self.board.animating)
        self.assertEqual(sum(self.match.engine.scores), 25)
        self.assertFalse(self.match.controller.active)
        self.finish()
        self.assertEqual(len(self.match.engine.history), 60)
        self.assertFalse(self.board.input_enabled)
        self.assertFalse(self.match.timers)

    def test_system_preference_is_default_and_user_override_wins(self):
        other = SetupStore(Path(self.temp.name) / "system-default.json")
        with patch("ui.qt_app.system_reduced_motion", return_value=True):
            window = PaperClubWindow(other)
            self.addCleanup(window.close)
            self.assertTrue(window.motion.reduced_motion)
            other.save_reduced_motion(False)
            override = PaperClubWindow(other)
            self.addCleanup(override.close)
            self.assertFalse(override.motion.reduced_motion)


if __name__ == "__main__":
    unittest.main()
