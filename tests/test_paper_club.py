from io import StringIO
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QFontDatabase
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from core.game_engine import MatchConfig
from ui.qt_app import PaperClubWindow
from utils.setup_preferences import SetupStore


class PaperClubFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        if os.name == "nt" and "Segoe UI" not in QFontDatabase.families():
            QFontDatabase.addApplicationFont(str(Path(os.environ.get("WINDIR", "C:/Windows"))
                                                 / "Fonts" / "segoeui.ttf"))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = SetupStore(Path(self.temp.name) / "settings.json")
        self.window = PaperClubWindow(self.store)
        self.addCleanup(self.window.close)
        self.addCleanup(self.window.match.stop)
        self.window.show()
        self.app.processEvents()

    def test_play_opens_setup_and_back_restores_home(self):
        self.window.play_button.click()
        self.assertIs(self.window.pages.currentWidget(), self.window.setup)
        self.assertFalse(self.window.match.controller.active)
        self.window.setup.back_button.click()
        self.assertIs(self.window.pages.currentWidget(), self.window.home)

    def test_opponent_switching_preserves_the_edited_friend_name(self):
        setup = self.window.setup
        setup.pvp_button.click()
        setup.player_two.setText("Robin")
        setup.pvp_button.click()
        self.assertEqual(setup.player_two.text(), "Robin")
        setup.ai_button.click()
        self.assertEqual(setup.player_two.text(), "Computer")
        self.assertFalse(setup.player_two.isEnabled())
        setup.pvp_button.click()
        self.assertEqual(setup.player_two.text(), "Robin")
        self.assertTrue(setup.player_two.isEnabled())

    def test_ai_start_forwards_names_and_difficulty_and_remembers_choices(self):
        self.window.show_setup()
        setup = self.window.setup
        setup.player_one.setText("  Élan  ")
        setup.difficulty_buttons["hard"].click()
        setup.start_button.click()
        config = MatchConfig("AI", "hard", ("Élan", "Computer"))
        self.assertIs(self.window.pages.currentWidget(), self.window.match)
        self.assertEqual(self.window.match.controller.config, config)
        self.assertTrue(self.window.match.controller.active)
        self.assertEqual(self.store.load().player_one, "Élan")
        self.assertEqual(self.store.load().difficulty, "hard")

    def test_local_setup_round_trip_and_keyboard_start(self):
        self.window.show_setup()
        setup = self.window.setup
        setup.pvp_button.click()
        setup.player_one.setText("Sam")
        setup.player_two.setText("Robin")
        QTest.keyClick(setup.player_two, Qt.Key.Key_Return)
        self.assertIs(self.window.pages.currentWidget(), self.window.match)
        self.assertEqual(self.window.match.controller.config,
                         MatchConfig("PVP", None, ("Sam", "Robin")))
        reopened = PaperClubWindow(self.store)
        self.addCleanup(reopened.close)
        self.assertTrue(reopened.setup.pvp_button.isChecked())
        self.assertEqual(reopened.setup.player_two.text(), "Robin")

    def test_empty_name_prevents_launch_and_focuses_invalid_field(self):
        self.window.show_setup()
        self.window.setup.player_one.setText("  ")
        self.window.setup.start_button.click()
        self.assertIs(self.window.pages.currentWidget(), self.window.setup)
        self.assertFalse(self.window.match.controller.active)
        self.assertTrue(self.window.setup.error.text())
        self.assertIs(self.window.focusWidget(), self.window.setup.player_one)

    def test_storage_failure_does_not_prevent_playing(self):
        self.window.show_setup()
        with patch.object(self.store, "save", return_value=False):
            self.window.setup.start_button.click()
        self.assertIn("could not be saved", self.window.setup.error.text())
        self.assertIs(self.window.pages.currentWidget(), self.window.match)
        self.assertTrue(self.window.match.controller.accepts_human_move)

    def test_screens_fit_compact_normal_and_wide_windows(self):
        for width, height in ((800, 480), (1100, 760), (1600, 900)):
            for page in (self.window.home, self.window.setup):
                with self.subTest(width=width, height=height, page=type(page).__name__):
                    self.window.resize(width, height)
                    self.window.pages.setCurrentWidget(page)
                    self.app.processEvents()
                    self.assertEqual((self.window.width(), self.window.height()), (width, height))
                    controls = ([self.window.play_button] if page is self.window.home else
                                [page.back_button, page.player_one, page.player_two,
                                 page.ai_button, page.pvp_button, page.start_button,
                                 *page.difficulty_buttons.values()])
                    for control in controls:
                        if control.isVisible():
                            bounds = QRect(control.mapTo(self.window, QPoint()), control.size())
                            self.assertTrue(self.window.rect().contains(bounds), control.objectName())
                            self.assertGreaterEqual(control.height(), 44)


class MatchLaunchTests(unittest.TestCase):
    def test_default_launch_and_paper_club_alias_open_qt(self):
        import main
        for arguments in ([], ["--paper-club"]):
            with self.subTest(arguments=arguments), \
                    patch("ui.qt_app.run", return_value=0) as run, patch.object(main, "Tk") as root:
                self.assertEqual(main.main(arguments), 0)
                run.assert_called_once_with()
                root.assert_not_called()

    def test_classic_flag_keeps_the_original_interface_available(self):
        import main
        root, manager = MagicMock(), MagicMock()
        with patch.object(main, "Tk", return_value=root), \
                patch.object(main, "ScreenManager", return_value=manager), \
                patch("ui.qt_app.run") as run:
            self.assertEqual(main.main(["--classic"]), 0)
        run.assert_not_called()
        root.mainloop.assert_called_once()

    def test_launch_arguments_reach_the_classic_match(self):
        import main
        root, manager = MagicMock(), MagicMock()
        with patch.object(main, "Tk", return_value=root), \
                patch.object(main, "ScreenManager", return_value=manager):
            self.assertEqual(main.main(["--mode", "AI", "--difficulty", "hard",
                                        "--player-one", "Sam", "--player-two", "Computer"]), 0)
        manager.show_screen.assert_called_once_with(
            "GameScreen", mode="AI", difficulty="hard", player_names=("Sam", "Computer"))
        root.mainloop.assert_called_once()

    def test_conflicting_launch_flags_are_rejected_before_a_window_opens(self):
        import main
        for arguments in (["--paper-club", "--mode", "AI"],
                          ["--paper-club", "--classic"], ["--difficulty", "hard"]):
            with self.subTest(arguments=arguments), patch.object(main, "Tk") as root, \
                    patch("sys.stderr", new_callable=StringIO), self.assertRaises(SystemExit):
                main.main(arguments)
            root.assert_not_called()


if __name__ == "__main__":
    unittest.main()
