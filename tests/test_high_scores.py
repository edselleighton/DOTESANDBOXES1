import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core.game_engine import MatchConfig
from utils.high_scores import (
    CAPACITY, HighScoreStore, PracticeRecord, ScoreRecord, match_record,
)


def ranked(match_id="m1", name="Alex", boxes=14, opponent="Casey", **kwargs):
    values = {"mode": "PVP", "difficulty": None, "completed_on": "2026-10-28"}
    values.update(kwargs)
    return ScoreRecord(match_id=match_id, name=name, boxes=boxes, opponent=opponent,
                       opponent_boxes=25 - boxes, **values)


class ScoreRecordTests(unittest.TestCase):
    def test_a_record_describes_one_finished_match(self):
        record = ranked(mode="AI", difficulty="hard", opponent="Computer")
        self.assertEqual(record.boxes + record.opponent_boxes, 25)
        self.assertEqual(record.opponent_label, "Computer (hard)")
        self.assertEqual(ranked().opponent_label, "Casey")

    def test_unfinished_tied_and_malformed_records_are_rejected(self):
        for kwargs in ({"boxes": 20, "opponent_boxes": 20}, {"boxes": 12, "opponent_boxes": 13},
                       {"boxes": 26, "opponent_boxes": -1}, {"boxes": 13.0, "opponent_boxes": 12},
                       {"boxes": True, "opponent_boxes": 24}, {"match_id": "  "},
                       {"match_id": 7}, {"name": ""}, {"name": "A" * 25}, {"opponent": "   "},
                       {"mode": "online"}, {"mode": "AI", "difficulty": None},
                       {"mode": "AI", "difficulty": "expert"},
                       {"mode": "PVP", "difficulty": "hard"},
                       {"completed_on": ""}, {"completed_on": "28-10-2026"},
                       {"completed_on": None}):
            values = {"match_id": "m1", "name": "Alex", "boxes": 13, "opponent": "Casey",
                      "opponent_boxes": 12, "mode": "PVP", "difficulty": None,
                      "completed_on": "2026-10-28"}
            values.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ScoreRecord(**values)

    def test_practice_records_count_attempts(self):
        self.assertEqual(PracticeRecord("p1", 3, "2026-10-28").attempts, 3)
        for kwargs in ({"attempts": 0}, {"attempts": -1}, {"attempts": 1000},
                       {"attempts": 1.0}, {"attempts": True}, {"match_id": ""},
                       {"completed_on": "today"}):
            values = {"match_id": "p1", "attempts": 2, "completed_on": "2026-10-28"}
            values.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                PracticeRecord(**values)

    def test_a_record_is_built_only_from_a_completed_match(self):
        config = MatchConfig("AI", "medium", ("Sam", "Computer"))
        record = match_record("m9", config, (13, 12), "2026-10-28")
        self.assertEqual((record.name, record.boxes, record.difficulty), ("Sam", 13, "medium"))
        self.assertEqual(record.opponent, "Computer")
        computer_led = match_record("m9", config, (11, 14), "2026-10-28")
        self.assertEqual((computer_led.name, computer_led.boxes), ("Computer", 14))
        for scores in ((0, 0), (12, 12), (13, 11), (25, 1)):
            with self.subTest(scores=scores):
                self.assertIsNone(match_record("m9", config, scores, "2026-10-28"))

    def test_a_local_match_records_no_difficulty(self):
        config = MatchConfig("PVP", None, ("Sam", "Robin"))
        self.assertIsNone(match_record("m2", config, (12, 13), "2026-10-28").difficulty)


class HighScoreStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "scores.json"
        self.store = HighScoreStore(self.path)

    def test_an_empty_or_damaged_file_reads_as_no_records(self):
        self.assertEqual(self.store.load_ranked(), ())
        self.assertEqual(self.store.load_practice(), ())
        self.assertIsNone(self.store.best_practice())
        for content in ("not json", "[]", '{"version": 2, "ranked": []}',
                        '{"version": 1, "ranked": {}}', '{"version": 1}',
                        '{"version": 1, "ranked": [null, 3, "row"]}'):
            with self.subTest(content=content):
                self.path.write_text(content, encoding="utf-8")
                self.assertEqual(self.store.load_ranked(), ())
                self.assertEqual(self.store.load_practice(), ())

    def test_records_round_trip_in_their_own_sections(self):
        match = ranked(mode="AI", difficulty="easy", opponent="Computer")
        practice = PracticeRecord("p1", 2, "2026-10-28")
        self.assertTrue(self.store.record_match(match))
        self.assertTrue(self.store.record_practice(practice))
        reopened = HighScoreStore(self.path)
        self.assertEqual(reopened.load_ranked(), (match,))
        self.assertEqual(reopened.load_practice(), (practice,))
        self.assertEqual(reopened.best_practice(), practice)

    def test_the_exercise_never_reaches_the_ranked_table(self):
        self.store.record_practice(PracticeRecord("p1", 1, "2026-10-28"))
        self.assertEqual(self.store.load_ranked(), ())
        self.assertFalse(self.store.record_match(PracticeRecord("p2", 1, "2026-10-28")))
        self.assertFalse(self.store.record_practice(ranked()))
        self.assertEqual(self.store.load_ranked(), ())
        self.assertEqual(len(self.store.load_practice()), 1)

    def test_the_same_match_identifier_is_recorded_once(self):
        record = ranked()
        self.assertTrue(self.store.record_match(record))
        self.assertTrue(self.store.record_match(record))
        self.assertTrue(self.store.record_match(ranked(name="Someone else")))
        self.assertEqual(self.store.load_ranked(), (record,))
        self.store.record_practice(PracticeRecord("p1", 4, "2026-10-28"))
        self.store.record_practice(PracticeRecord("p1", 1, "2026-10-29"))
        self.assertEqual(self.store.load_practice(), (PracticeRecord("p1", 4, "2026-10-28"),))

    def test_ranked_order_prefers_more_boxes_then_a_tighter_defence(self):
        records = [ranked("a", "Alex", 13), ranked("b", "Blair", 20),
                   ranked("c", "Casey", 20, completed_on="2026-10-20"),
                   ranked("d", "Dev", 25)]
        for record in records:
            self.store.record_match(record)
        self.assertEqual([record.name for record in self.store.load_ranked()],
                         ["Dev", "Casey", "Blair", "Alex"])

    def test_practice_order_prefers_fewer_attempts(self):
        for index, attempts in enumerate((5, 1, 3)):
            self.store.record_practice(PracticeRecord(f"p{index}", attempts, "2026-10-28"))
        self.assertEqual([record.attempts for record in self.store.load_practice()], [1, 3, 5])
        self.assertEqual(self.store.best_practice().attempts, 1)

    def test_only_the_best_records_are_kept(self):
        for index in range(CAPACITY + 6):
            self.store.record_match(ranked(f"m{index}", f"Player {index}", 13 + index % 12))
            self.store.record_practice(PracticeRecord(f"p{index}", index + 1, "2026-10-28"))
        self.assertEqual(len(self.store.load_ranked()), CAPACITY)
        self.assertEqual(len(self.store.load_practice()), CAPACITY)
        self.assertEqual(self.store.load_ranked()[0].boxes, 24)
        self.assertEqual(self.store.best_practice().attempts, 1)

    def test_rows_that_no_longer_satisfy_the_rules_are_skipped(self):
        self.store.record_match(ranked())
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data["ranked"].extend([{"match_id": "bad", "name": "", "boxes": 13,
                                "opponent": "Casey", "opponent_boxes": 12,
                                "mode": "PVP", "completed_on": "2026-10-28"},
                               {"match_id": "worse"}, {"name": "No identifier"}])
        data["practice"] = [{"match_id": "p1", "attempts": 0, "completed_on": "2026-10-28"},
                            {"match_id": "p2", "attempts": 2, "completed_on": "2026-10-28"}]
        self.path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual([record.name for record in self.store.load_ranked()], ["Alex"])
        self.assertEqual([record.match_id for record in self.store.load_practice()], ["p2"])

    def test_unknown_keys_and_extra_sections_are_left_alone(self):
        self.path.write_text(json.dumps({
            "version": 1, "future_section": {"kept": True},
            "ranked": [{"match_id": "m1", "name": "Alex", "boxes": 13, "opponent": "Casey",
                        "opponent_boxes": 12, "mode": "PVP", "completed_on": "2026-10-28",
                        "future_field": 1}],
        }), encoding="utf-8")
        self.assertEqual([record.name for record in self.store.load_ranked()], ["Alex"])
        self.assertTrue(self.store.record_practice(PracticeRecord("p1", 1, "2026-10-28")))
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["future_section"], {"kept": True})
        self.assertEqual(len(data["ranked"]), 1)

    def test_a_failed_atomic_replace_preserves_the_existing_records(self):
        record = ranked()
        self.store.record_match(record)
        original = self.path.read_bytes()
        with patch("utils.high_scores.os.replace", side_effect=PermissionError):
            self.assertFalse(self.store.record_match(ranked("m2", "Blair", 20)))
            self.assertFalse(self.store.record_practice(PracticeRecord("p1", 1, "2026-10-28")))
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(self.store.load_ranked(), (record,))
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_an_unwritable_location_does_not_raise(self):
        blocker = Path(self.temp.name) / "file-not-directory"
        blocker.write_text("occupied", encoding="utf-8")
        store = HighScoreStore(blocker / "scores.json")
        self.assertFalse(store.record_match(ranked()))
        self.assertEqual(store.load_ranked(), ())

    def test_the_default_location_sits_beside_the_settings_file(self):
        self.assertEqual(HighScoreStore().path.name, "scores.json")
        self.assertEqual(HighScoreStore().path.parent.name, "DotsAndBoxes")


if __name__ == "__main__":
    unittest.main()
