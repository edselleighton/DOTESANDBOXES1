"""Verify the instructions exercise, the high scores sheet, and what is recorded."""
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
from ui.practice_page import GOAL, SETUP
from ui.qt_app import PaperClubWindow
from utils.high_scores import HighScoreStore, PracticeRecord
from utils.setup_preferences import SetupStore
from test_game_engine import all_moves


class PracticeAndScoresTests(unittest.TestCase):
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
        self.scores = HighScoreStore(Path(self.temp.name) / "scores.json")
        self.window = PaperClubWindow(self.store, audio=quiet_audio(self.store),
                                      score_store=self.scores)
        self.addCleanup(self.window.close)
        self.window.resize(1180, 780)
        self.window.show()
        self.app.processEvents()

    def finish_match(self, config):
        """Play a whole match, letting real computer turns run without a delay."""
        self.window.start_match(config)
        self.app.processEvents()
        match = self.window.match
        match.controller._ai_delay_ms = 0
        for _ in range(400):
            if match.engine.finished:
                break
            if match.controller.accepts_human_move:
                move = next(move for move in all_moves() if match.engine.is_legal(move))
                match.play_human(move)
            self.app.processEvents()
        self.assertTrue(match.engine.finished)
        self.assertEqual(sum(match.engine.scores), 25)
        return match

    def test_scores_default_to_the_settings_folder_but_can_be_supplied(self):
        default = PaperClubWindow(self.store, audio=quiet_audio(self.store))
        self.addCleanup(default.close)
        self.assertEqual(default.score_store.path, Path(self.temp.name) / "scores.json")
        self.assertIs(self.window.score_store, self.scores)

    def test_the_high_scores_entry_opens_the_sheet_and_explains_an_empty_table(self):
        button = self.window.home.scores_button
        self.assertTrue(button.isEnabled())
        self.assertTrue(button.accessibleDescription())
        button.click()
        self.app.processEvents()
        self.assertIs(self.window.pages.currentWidget(), self.window.scores)
        self.assertEqual(self.window.scores.rows, ())
        self.assertIn("No finished matches yet", self.window.scores.ranked_message.text())
        self.assertIn("not been completed yet", self.window.scores.practice_summary.text())
        QTest.keyClick(self.window, Qt.Key.Key_Escape)
        self.app.processEvents()
        self.assertIs(self.window.pages.currentWidget(), self.window.home)

    def test_a_completed_match_is_recorded_once_and_listed(self):
        match = self.finish_match(MatchConfig("AI", "hard", ("Sam", "Computer")))
        recorded = self.scores.load_ranked()
        self.assertEqual(len(recorded), 1)
        self.assertEqual(sum((recorded[0].boxes, recorded[0].opponent_boxes)), 25)
        self.assertEqual(recorded[0].mode, "AI")
        self.assertEqual(recorded[0].difficulty, "hard")
        self.assertEqual(recorded[0].match_id, match.match_id)
        # A repeated completion callback must not add the same match again.
        match.match_finished.emit(match.match_id)
        self.assertEqual(self.scores.load_ranked(), recorded)
        self.window.show_scores()
        self.app.processEvents()
        rows = self.window.scores.rows
        self.assertEqual(len(rows), 1)
        self.assertIsNone(self.window.scores.ranked_message)
        self.assertTrue(rows[0].accessibleName().startswith("1. "))
        self.assertIn(str(recorded[0].boxes), rows[0].accessibleName())

    def test_a_rematch_is_recorded_as_its_own_match(self):
        match = self.finish_match(MatchConfig("PVP", None, ("Alex", "Casey")))
        first = match.match_id
        match.rematch_button.click()
        self.app.processEvents()
        self.assertNotEqual(match.match_id, first)
        for move in all_moves():
            match.play_human(move)
        self.app.processEvents()
        self.assertEqual({record.match_id for record in self.scores.load_ranked()},
                         {first, match.match_id})

    def test_an_abandoned_match_is_not_recorded(self):
        self.window.start_match(MatchConfig("PVP", None, ("Alex", "Casey")))
        match = self.window.match
        for move in list(all_moves())[:12]:
            match.play_human(move)
        with patch("ui.qt_app.QMessageBox.question",
                   return_value=QMessageBox.StandardButton.Discard):
            self.window.show_home()
        self.app.processEvents()
        self.assertEqual(match.match_id, "")
        self.assertEqual(self.scores.load_ranked(), ())
        self.window.home.scores_button.click()
        self.app.processEvents()
        self.assertIn("leave early", self.window.scores.ranked_message.text())

    def test_a_failed_save_leaves_play_available(self):
        with patch("utils.high_scores.os.replace", side_effect=PermissionError):
            match = self.finish_match(MatchConfig("PVP", None, ("Alex", "Casey")))
        self.assertEqual(self.scores.load_ranked(), ())
        self.assertIn("could not be added", self.window.statusBar().currentMessage())
        self.assertTrue(match.rematch_button.isEnabled())

    def test_the_exercise_starts_from_three_drawn_sides(self):
        self.window.settings.practice_button.click()
        self.app.processEvents()
        practice = self.window.practice
        self.assertIs(self.window.pages.currentWidget(), practice)
        self.assertEqual(len(practice.engine.history), len(SETUP))
        self.assertEqual(practice.engine.scores, (0, 0))
        self.assertTrue(practice.engine.is_legal(GOAL))
        self.assertEqual(practice.engine.current_player, 1)
        self.assertEqual(practice.attempts, 0)
        self.assertIn("fourth side", practice.guidance.text())

    def test_only_the_missing_side_closes_the_box_and_is_counted(self):
        self.window.show_practice()
        practice = self.window.practice
        other = next(move for move in all_moves()
                     if move != GOAL and practice.engine.is_legal(move))
        self.assertIsNone(practice.play(other))
        self.assertEqual(practice.attempts, 1)
        self.assertEqual(len(practice.engine.history), len(SETUP))
        self.assertEqual(practice.engine.scores, (0, 0))
        self.assertIn("does not close", practice.guidance.text())
        self.assertFalse(practice.finished)
        outcome = practice.play(GOAL)
        self.app.processEvents()
        self.assertEqual(outcome.captured_boxes, ((2, 2),))
        self.assertEqual(practice.engine.scores, (1, 0))
        self.assertTrue(practice.finished)
        self.assertEqual(practice.attempts, 2)
        self.assertIn("another turn", practice.guidance.text())
        self.assertFalse(practice.reveal_button.isEnabled())
        self.assertIsNone(practice.play(GOAL))
        self.assertEqual(practice.engine.scores, (1, 0))

    def test_a_finished_exercise_is_recorded_as_practice_only(self):
        self.window.show_practice()
        practice = self.window.practice
        practice.play(GOAL)
        self.app.processEvents()
        recorded = self.scores.load_practice()
        self.assertEqual(len(recorded), 1)
        self.assertEqual(recorded[0].attempts, 1)
        self.assertEqual(self.scores.load_ranked(), ())
        self.assertEqual(recorded[0].match_id, practice._run_id)

    def test_starting_over_records_a_separate_run_and_keeps_the_best(self):
        self.window.show_practice()
        practice = self.window.practice
        practice.play(GOAL)
        first = practice._run_id
        practice.restart_button.click()
        self.app.processEvents()
        self.assertNotEqual(practice._run_id, first)
        self.assertFalse(practice.finished)
        self.assertEqual(practice.attempts, 0)
        self.assertEqual(len(practice.engine.history), len(SETUP))
        other = next(move for move in all_moves()
                     if move != GOAL and practice.engine.is_legal(move))
        practice.play(other)
        practice.play(GOAL)
        self.app.processEvents()
        self.assertEqual([record.attempts for record in self.scores.load_practice()], [1, 2])
        self.assertEqual(self.scores.best_practice().attempts, 1)

    def test_reveal_marks_the_missing_side_without_drawing_it(self):
        self.window.show_practice()
        practice = self.window.practice
        practice.reveal_button.click()
        self.assertEqual(practice.board.hint, GOAL)
        self.assertEqual(len(practice.engine.history), len(SETUP))
        self.assertEqual(practice.attempts, 0)

    def test_keyboard_play_completes_the_exercise(self):
        self.window.show_practice()
        practice = self.window.practice
        practice.board.setFocus()
        self.app.processEvents()
        self.assertEqual(practice.board.selected, GOAL)
        QTest.keyClick(practice.board, Qt.Key.Key_Return)
        self.app.processEvents()
        self.assertTrue(practice.finished)
        self.assertEqual(practice.engine.scores, (1, 0))

    def test_the_exercise_returns_to_where_it_was_opened_from(self):
        self.window.settings.practice_button.click()
        self.app.processEvents()
        self.window.practice.done_button.click()
        self.app.processEvents()
        self.assertIs(self.window.pages.currentWidget(), self.window.settings)
        self.assertEqual(self.window.settings.tabs.currentIndex(), 1)
        self.window.settings.done_button.click()
        self.window.home.scores_button.click()
        self.window.scores.practice_button.click()
        self.app.processEvents()
        self.assertIs(self.window.pages.currentWidget(), self.window.practice)
        QTest.keyClick(self.window, Qt.Key.Key_Escape)
        self.app.processEvents()
        self.assertIs(self.window.pages.currentWidget(), self.window.scores)

    def test_a_completed_run_appears_on_the_sheet_after_returning(self):
        self.window.home.scores_button.click()
        self.window.scores.practice_button.click()
        self.app.processEvents()
        self.window.practice.play(GOAL)
        self.window.practice.done_button.click()
        self.app.processEvents()
        self.assertIs(self.window.pages.currentWidget(), self.window.scores)
        self.assertIn("Best run: 1 attempt", self.window.scores.practice_summary.text())

    def test_the_exercise_waits_for_a_paused_match_to_be_resumed_or_left(self):
        self.window.start_match(MatchConfig("PVP", None, ("Alex", "Casey")))
        match = self.window.match
        match.play_human(Move("row", (0, 0)))
        self.window.show_settings(1)
        self.app.processEvents()
        self.assertTrue(match.controller.paused)
        self.assertFalse(self.window.settings.practice_button.isEnabled())
        self.assertIn("Resume or leave",
                      self.window.settings.practice_button.accessibleDescription())
        self.window.settings.done_button.click()
        self.window.pause_panel.resume.click()
        self.app.processEvents()
        self.assertEqual(len(match.engine.history), 1)
        with patch("ui.qt_app.QMessageBox.question",
                   return_value=QMessageBox.StandardButton.Cancel):
            self.window.show_practice()
        self.assertIs(self.window.pages.currentWidget(), match)
        self.assertEqual(len(match.engine.history), 1)
        self.window.show_settings(1)
        self.app.processEvents()
        self.assertFalse(self.window.settings.practice_button.isEnabled())

    def test_the_new_sheets_fit_compact_and_wide_windows(self):
        self.finish_match(MatchConfig("AI", "easy", ("Alexandra Paper Champion", "Computer")))
        self.window.show_practice()
        self.window.practice.play(GOAL)
        for width, height in ((800, 480), (1180, 780), (1920, 1080)):
            self.window.resize(width, height)
            for page, controls in (
                (self.window.scores, lambda page: (page.back_button, page.practice_button,
                                                   page.done_button)),
                (self.window.practice, lambda page: (page.back_button, page.reveal_button,
                                                     page.restart_button, page.done_button)),
            ):
                self.window.pages.setCurrentWidget(page)
                if page is self.window.scores:
                    page.refresh(self.scores.load_ranked(), self.scores.best_practice())
                self.app.processEvents()
                for control in controls(page):
                    bounds = QRect(control.mapTo(self.window, QPoint()), control.size())
                    self.assertTrue(self.window.rect().contains(bounds),
                                    (width, height, control.text()))
                    self.assertGreaterEqual(control.height(), 44)
            board = self.window.practice.board
            self.assertEqual(board.width(), board.height())
            self.assertGreater(board.width(), 100)

    def test_records_survive_a_restart_and_reach_a_fresh_window(self):
        self.finish_match(MatchConfig("PVP", None, ("Alex", "Casey")))
        self.window.show_practice()
        self.window.practice.play(GOAL)
        self.app.processEvents()
        self.window.close()
        reopened = PaperClubWindow(self.store, audio=quiet_audio(self.store))
        self.addCleanup(reopened.close)
        reopened.resize(1180, 780)
        reopened.show()
        reopened.home.scores_button.click()
        self.app.processEvents()
        self.assertEqual(len(reopened.score_store.load_ranked()), 1)
        self.assertEqual(reopened.score_store.best_practice(),
                         PracticeRecord(reopened.score_store.best_practice().match_id, 1,
                                        self.scores.best_practice().completed_on))
        self.assertIn("Best run", reopened.scores.practice_summary.text())


if __name__ == "__main__":
    unittest.main()
