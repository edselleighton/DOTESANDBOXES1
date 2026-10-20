import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from utils.setup_preferences import SetupChoices, SetupStore


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


if __name__ == "__main__":
    unittest.main()
