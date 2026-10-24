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


    def test_reduced_motion_round_trip_overrides_system_default(self):
        for enabled in (True, False):
            with self.subTest(enabled=enabled):
                self.assertTrue(self.store.save_reduced_motion(enabled))
                self.assertIs(SetupStore(self.path).load_reduced_motion(not enabled), enabled)

    def test_missing_or_malformed_motion_preference_uses_system_default(self):
        self.assertFalse(self.store.load_reduced_motion())
        self.assertTrue(self.store.load_reduced_motion(True))
        for content in (
            "broken json", "[]", '{"version":2,"display":{"reduced_motion":false}}',
            '{"version":1}', '{"version":1,"display":null}',
            '{"version":1,"display":[]}', '{"version":1,"display":{}}',
        ):
            with self.subTest(content=content):
                self.path.write_text(content, encoding="utf-8")
                self.assertTrue(self.store.load_reduced_motion(True))
                self.assertFalse(self.store.load_reduced_motion(False))
        for value in (None, 0, 1, "false", "true", [], {}):
            with self.subTest(value=value):
                self.path.write_text(json.dumps({
                    "version": 1, "display": {"reduced_motion": value},
                }), encoding="utf-8")
                self.assertTrue(self.store.load_reduced_motion(True))
                self.assertFalse(self.store.load_reduced_motion(False))

    def test_motion_save_preserves_other_display_and_settings_values(self):
        self.path.write_text(json.dumps({
            "version": 1, "audio": {"music": 15},
            "display": {"contrast": "strong", "future_option": {"value": 3}},
        }), encoding="utf-8")
        choices = SetupChoices("PVP", "hard", "Sam", "Robin")
        window = WindowPreferences(False, True, 1180, 780)
        self.assertTrue(self.store.save(choices))
        self.assertTrue(self.store.save_window(window))
        self.assertTrue(self.store.save_reduced_motion(True))
        self.assertEqual(self.store.load(), choices)
        self.assertEqual(self.store.load_window(), window)
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["audio"], {"music": 15})
        self.assertEqual(data["display"], {
            "reduced_motion": True, "contrast": "strong", "future_option": {"value": 3},
        })
        self.assertTrue(self.store.save(SetupChoices()))
        self.assertTrue(self.store.save_window(WindowPreferences()))
        self.assertTrue(self.store.load_reduced_motion())

    def test_motion_save_repairs_invalid_display_section(self):
        for display in (None, [], "invalid"):
            with self.subTest(display=display):
                self.path.write_text(json.dumps({"version": 1, "display": display}),
                                     encoding="utf-8")
                self.assertTrue(self.store.save_reduced_motion(True))
                self.assertTrue(self.store.load_reduced_motion())

    def test_invalid_motion_arguments_do_not_coerce_truthiness(self):
        self.store.save_reduced_motion(True)
        original = self.path.read_bytes()
        for value in (None, 0, 1, "false", [], {}):
            with self.subTest(value=value):
                self.assertFalse(self.store.save_reduced_motion(value))
                self.assertEqual(self.path.read_bytes(), original)
                with self.assertRaises(ValueError):
                    self.store.load_reduced_motion(value)

    def test_failed_motion_save_preserves_existing_file(self):
        self.store.save(SetupChoices("PVP", "easy", "Sam", "Robin"))
        self.store.save_reduced_motion(False)
        original = self.path.read_bytes()
        with patch("utils.setup_preferences.os.replace", side_effect=PermissionError):
            self.assertFalse(self.store.save_reduced_motion(True))
        self.assertEqual(self.path.read_bytes(), original)
        self.assertFalse(self.store.load_reduced_motion(True))
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
