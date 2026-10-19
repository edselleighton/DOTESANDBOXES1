"""Exercise real widget wiring without opening windows on the desktop."""

import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase, QRawFont

from core.game_engine import Move
from test_game_engine import all_moves
from ui.qt_app import PaperClubWindow, classic_command


class ClassicGameIntegrationTests(unittest.TestCase):
    def setUp(self):
        from tkinter import Tk
        from main import ScreenManager
        self.root = Tk()
        self.root.withdraw()
        self.manager = ScreenManager(self.root)
        self.game = self.manager.screens["GameScreen"]

    def tearDown(self):
        self.game.controller.stop()
        self.root.destroy()

    def click(self, move):
        sx, sy, ex, ey = self.game.renderer.geometry.edge_points(move)
        self.game.on_click(SimpleNamespace(x=(sx + ex) / 2, y=(sy + ey) / 2))

    def test_local_match_uses_shared_rules_and_opens_results(self):
        self.manager.show_screen("GameScreen", mode="PVP")
        for move in all_moves():
            self.click(move)
        self.assertEqual(len(self.game.engine.history), 60)
        self.assertFalse(self.game.controller.active)
        result = self.manager.screens["ResultScreen"]
        self.assertEqual(int(result.lbl_p1_score.cget("text"))
                         + int(result.lbl_p2_score.cget("text")), 25)
        self.assertEqual(result.place_info()["relwidth"], "1")

    def test_navigation_cancels_ai_and_resets_new_match(self):
        self.manager.show_screen("GameScreen", mode="AI", difficulty="easy")
        self.click(Move("row", (0, 0)))
        self.click(Move("row", (1, 0)))
        self.assertEqual(len(self.game.engine.history), 1)
        self.assertEqual(str(self.game.hint_button.cget("state")), "disabled")
        self.assertTrue(self.root.tk.call("after", "info"))
        self.manager.show_screen("ModeSelect")
        self.assertFalse(self.root.tk.call("after", "info"))
        self.manager.show_screen("GameScreen", mode="PVP")
        self.assertEqual(self.game.engine.history, ())
        self.assertEqual(self.game.p1_score_label.cget("text"), "0")
        self.click(Move("row", (0, 0)))
        self.assertEqual(str(self.game.undo_button.cget("state")), "normal")
        self.assertTrue(self.game.undo_move())

    def test_hint_and_margin_click_do_not_change_the_board(self):
        self.manager.show_screen("GameScreen", mode="PVP")
        self.game.on_click(SimpleNamespace(x=0, y=560 / 12))
        self.assertEqual(self.game.engine.history, ())
        self.game.show_hint()
        self.assertTrue(self.game.canvas.find_withtag("hint"))
        self.click(Move("row", (0, 0)))
        self.assertFalse(self.game.canvas.find_withtag("hint"))


class QtShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        # Qt's offscreen Windows plugin does not discover installed fonts itself.
        if os.name == "nt" and not QFontDatabase.families():
            font = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "segoeui.ttf"
            if QFontDatabase.addApplicationFont(str(font)) < 0:
                raise RuntimeError("Cannot load the Windows font for offscreen tests")

    def setUp(self):
        self.window = PaperClubWindow()

    def tearDown(self):
        self.window.close()

    def test_shell_layout_fits_small_and_large_windows(self):
        self.assertTrue(QRawFont.fromFont(QFont("Segoe UI")).supportsCharacter(ord("D")))
        for width, height in ((800, 480), (1100, 760), (1600, 900)):
            with self.subTest(width=width, height=height):
                self.window.resize(width, height)
                self.window.show()
                self.app.processEvents()
                page = self.window.pages.currentWidget()
                self.assertTrue(page.rect().contains(self.window.play_button.geometry()))
                self.assertGreaterEqual(self.window.play_button.height(), 44)
                self.assertTrue(self.window.play_button.accessibleDescription())

    def test_fullscreen_restores_maximized_state(self):
        self.window.showMaximized()
        self.app.processEvents()
        self.window.fullscreen_action.setChecked(True)
        self.app.processEvents()
        self.assertTrue(self.window.isFullScreen())
        self.window.leave_fullscreen()
        self.app.processEvents()
        self.assertTrue(self.window.isMaximized())
        self.assertFalse(self.window.fullscreen_action.isChecked())

    def test_play_launches_the_current_game_without_preview_flag(self):
        with patch("ui.qt_app.QProcess.startDetached", return_value=(True, 123)) as start:
            self.window.play_button.click()
        program, arguments = classic_command()
        start.assert_called_once_with(program, arguments)
        self.assertNotIn("--paper-club", arguments)


if __name__ == "__main__":
    unittest.main()
