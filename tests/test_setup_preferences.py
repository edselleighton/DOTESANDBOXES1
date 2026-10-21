import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from utils.setup_preferences import SetupChoices, SetupStore, WindowPreferences


class SetupPreferencesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "settings.json"
        self.store = SetupStore(self.path)

    def test_missing_or_damaged_settings_use_defaults(self):
        self.assertEqual(self.store.load(), SetupChoices())
        for content in ("not json", "[]", '{"version": 3}',
                        '{"version":1,"setup":{"mode":"online"}}',
                        '{"version":1,"setup":{"player_one":null}}',
                        '{"version":1,"setup":{"difficulty":"expert"}}'):
            with self.subTest(content=content):
                self.path.write_text(content, encoding="utf-8")
                self.assertEqual(self.store.load(), SetupChoices())

    def test_names_mode_and_difficulty_round_trip(self):
        choices = SetupChoices("PVP", "hard", "Élan", "Jo")
        self.assertTrue(self.store.save(choices))
        self.assertEqual(SetupStore(self.path).load(), choices)

    def test_ai_keeps_the_friend_name_for_later_local_games(self):
        choices = SetupChoices("AI", "easy", "Sam", "Robin")
        config = choices.match_config()
        self.assertEqual(config.player_names, ("Sam", "Computer"))
        self.assertEqual(config.difficulty, "easy")
        self.assertTrue(self.store.save(choices))
        self.assertEqual(self.store.load().player_two, "Robin")

    def test_local_match_does_not_apply_an_ai_difficulty(self):
        config = SetupChoices("PVP", "hard", "Sam", "Robin").match_config()
        self.assertIsNone(config.difficulty)
        self.assertEqual(config.player_names, ("Sam", "Robin"))

    def test_saving_preserves_other_settings(self):
        self.path.write_text(json.dumps({"version": 1, "audio": {"music": 15}}))
        self.assertTrue(self.store.save(SetupChoices()))
        self.assertEqual(json.loads(self.path.read_text())["audio"], {"music": 15})

    def test_failed_atomic_replace_preserves_existing_settings(self):
        original = SetupChoices("AI", "easy", "Sam", "Robin")
        self.store.save(original)
        with patch("utils.setup_preferences.os.replace", side_effect=PermissionError):
            self.assertFalse(self.store.save(SetupChoices()))
        self.assertEqual(self.store.load(), original)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_unwritable_location_does_not_raise(self):
        blocker = Path(self.temp.name) / "file-not-directory"
        blocker.write_text("occupied")
        self.assertFalse(SetupStore(blocker / "settings.json").save(SetupChoices()))

    def test_invalid_names_are_rejected(self):
        for name in ("", "   ", "A" * 25):
            with self.subTest(name=name), self.assertRaises(ValueError):
                SetupChoices(player_one=name)

    def test_first_launch_defaults_to_fullscreen(self):
        preferences = self.store.load_window()
        self.assertTrue(preferences.fullscreen)
        self.assertFalse(preferences.maximized)
        self.assertEqual((preferences.width, preferences.height), (1180, 780))

    def test_window_preferences_round_trip(self):
        for preferences in (WindowPreferences(False, False, 950, 620),
                            WindowPreferences(False, True, 1180, 780),
                            WindowPreferences(True, True, 1180, 780)):
            with self.subTest(preferences=preferences):
                self.assertTrue(self.store.save_window(preferences))
                self.assertEqual(SetupStore(self.path).load_window(), preferences)

    def test_invalid_window_settings_fall_back_to_fullscreen(self):
        for value in (None, [], "fullscreen", {"fullscreen": "false"},
                      {"maximized": 1}, {"width": True}, {"height": 480.5},
                      {"width": 799}, {"height": 479}, {"width": 999999},
                      {"width": None}):
            with self.subTest(value=value):
                self.path.write_text(json.dumps({"version": 1, "window": value}),
                                     encoding="utf-8")
                self.assertEqual(self.store.load_window(), WindowPreferences())
        for content in ("broken json", "[]", '{"version":2,"window":{"fullscreen":false}}'):
            with self.subTest(content=content):
                self.path.write_text(content, encoding="utf-8")
                self.assertEqual(self.store.load_window(), WindowPreferences())

    def test_partial_window_settings_keep_defaults_and_ignore_unknown_keys(self):
        self.path.write_text(json.dumps({
            "version": 1, "window": {"fullscreen": False, "future_setting": True},
        }), encoding="utf-8")
        self.assertEqual(self.store.load_window(), WindowPreferences(fullscreen=False))

    def test_setup_window_and_other_settings_preserve_each_other(self):
        self.path.write_text(json.dumps({"version": 1, "audio": {"music": 15}}),
                             encoding="utf-8")
        choices = SetupChoices("PVP", "hard", "Sam", "Robin")
        preferences = WindowPreferences(False, False, 950, 620)
        self.assertTrue(self.store.save(choices))
        self.assertTrue(self.store.save_window(preferences))
        self.assertEqual(self.store.load(), choices)
        updated_choices = SetupChoices("AI", "easy", "Sam", "Robin")
        self.assertTrue(self.store.save(updated_choices))
        self.assertEqual(self.store.load_window(), preferences)
        self.assertEqual(self.store.load(), updated_choices)
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["audio"],
                         {"music": 15})

    def test_failed_window_save_preserves_both_sections(self):
        choices = SetupChoices("PVP", "hard", "Sam", "Robin")
        preferences = WindowPreferences(False, True, 1180, 780)
        self.store.save(choices)
        self.store.save_window(preferences)
        with patch("utils.setup_preferences.os.replace", side_effect=PermissionError):
            self.assertFalse(self.store.save_window(WindowPreferences()))
        self.assertEqual(self.store.load(), choices)
        self.assertEqual(self.store.load_window(), preferences)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_unwritable_window_settings_do_not_raise(self):
        blocker = Path(self.temp.name) / "file-not-directory"
        blocker.write_text("occupied", encoding="utf-8")
        self.assertFalse(SetupStore(blocker / "settings.json").save_window(WindowPreferences()))


if __name__ == "__main__":
    unittest.main()
