import unittest
import subprocess
import sys

import numpy as np

from core.game_engine import GameEngine, MatchConfig, Move
from ui.board_geometry import BoardGeometry


def all_moves():
    for edge, width, height in (("row", 5, 6), ("col", 6, 5)):
        for x in range(width):
            for y in range(height):
                yield Move(edge, (x, y))


def prepare_box(engine):
    for move in (Move("row", (0, 0)), Move("col", (0, 0)), Move("row", (0, 1))):
        engine.play(move)


class GameRulesTests(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine()

    def test_rules_import_without_loading_a_gui_runtime(self):
        subprocess.run([
            sys.executable, "-c",
            "import sys; from core.game_engine import GameEngine; "
            "assert GameEngine().scores == (0, 0); "
            "assert 'tkinter' not in sys.modules; "
            "assert 'PySide6' not in sys.modules",
        ], check=True)

    def test_invalid_and_occupied_moves_preserve_state_and_turn(self):
        invalid = (Move("row", (-1, 0)), Move("col", (6, 0)),
                   Move("row", (5, 0)), Move("col", (0, 5)),
                   Move("diagonal", (0, 0)), Move("row", (0.5, 0)),
                   Move("row", (False, 0)), Move("row", (0,)), None)
        for move in invalid:
            with self.subTest(move=move):
                self.assertIsNone(self.engine.play(move))
        self.assertEqual(self.engine.current_player, 1)
        self.assertEqual(self.engine.history, ())
        self.assertFalse(np.any(self.engine.row_status))
        self.assertFalse(np.any(self.engine.col_status))
        move = Move("row", (0, 0))
        self.engine.play(move)
        self.assertIsNone(self.engine.play(move))
        self.assertEqual(len(self.engine.history), 1)
        self.assertEqual(self.engine.current_player, 2)

    def test_capture_scores_once_and_keeps_the_turn(self):
        prepare_box(self.engine)
        outcome = self.engine.play(Move("col", (1, 0)))
        self.assertEqual(outcome.captured_boxes, ((0, 0),))
        self.assertEqual(outcome.player, 2)
        self.assertEqual(outcome.next_player, 2)
        self.assertEqual(outcome.scores, (0, 1))
        self.assertFalse(outcome.finished)
        self.assertFalse(self.engine.undo_move())

    def test_shared_edge_can_capture_two_boxes(self):
        for move in (Move("row", (0, 0)), Move("row", (1, 0)),
                     Move("row", (0, 1)), Move("row", (1, 1)),
                     Move("col", (0, 0)), Move("col", (2, 0))):
            self.engine.play(move)
        outcome = self.engine.play(Move("col", (1, 0)))
        self.assertEqual(outcome.captured_boxes, ((0, 0), (1, 0)))
        self.assertEqual(outcome.scores, (2, 0))
        self.assertEqual(self.engine.current_player, 1)

    def test_non_scoring_move_after_a_capture_can_still_be_undone(self):
        prepare_box(self.engine)
        self.engine.play(Move("col", (1, 0)))
        outcome = self.engine.play(Move("row", (3, 3)))
        self.assertEqual(outcome.captured_boxes, ())
        self.assertTrue(self.engine.undo_move())
        self.assertEqual(self.engine.current_player, 2)
        self.assertEqual(self.engine.scores, (0, 1))
        self.assertEqual(self.engine.row_status[3, 3], 0)
        self.assertEqual(len(self.engine.history), 4)
        self.assertFalse(self.engine.undo_move())

    def test_all_sixty_edges_finish_with_exactly_twenty_five_boxes(self):
        outcomes = [self.engine.play(move) for move in all_moves()]
        self.assertEqual(sum(len(o.captured_boxes) for o in outcomes), 25)
        self.assertTrue(outcomes[-1].finished)
        self.assertTrue(self.engine.finished)
        self.assertEqual(sum(self.engine.scores), 25)
        self.assertIsNone(self.engine.ai_move("hard"))
        self.assertIsNone(self.engine.get_hint())
        self.assertIsNone(self.engine.play(Move("row", (0, 0))))
        self.assertEqual(len(self.engine.history), 60)

    def test_hint_preserves_state_and_hard_uses_the_same_strategy(self):
        prepare_box(self.engine)
        before = [array.copy() for array in (
            self.engine.row_status, self.engine.col_status, self.engine.box_owner)]
        player, history = self.engine.current_player, self.engine.history
        hint = self.engine.get_hint()
        self.assertTrue(self.engine.is_legal(hint))
        for array, expected in zip((self.engine.row_status, self.engine.col_status,
                                    self.engine.box_owner), before):
            np.testing.assert_array_equal(array, expected)
        self.assertEqual(self.engine.current_player, player)
        self.assertEqual(self.engine.history, history)
        self.assertEqual(self.engine.ai_move("hard").move, hint)

    def test_medium_takes_an_available_box(self):
        prepare_box(self.engine)
        outcome = self.engine.ai_move("medium")
        self.assertEqual(outcome.move, Move("col", (1, 0)))
        self.assertEqual(outcome.captured_boxes, ((0, 0),))

    def test_reset_clears_state_without_replacing_ai_arrays(self):
        original_rows = self.engine.row_status
        prepare_box(self.engine)
        self.engine.play(Move("col", (1, 0)))
        self.engine.reset()
        self.assertIs(self.engine.row_status, original_rows)
        self.assertEqual(self.engine.scores, (0, 0))
        self.assertEqual(self.engine.history, ())
        self.assertEqual(self.engine.current_player, 1)
        self.assertFalse(np.any(self.engine.row_status))
        self.assertFalse(np.any(self.engine.col_status))

    def test_configuration_rejects_unknown_modes_and_difficulties(self):
        self.assertEqual(MatchConfig(mode="AI").difficulty, "medium")
        for kwargs in ({"mode": "online"}, {"difficulty": "impossible"},
                       {"player_names": ("", "Player 2")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                MatchConfig(**kwargs)


class BoardGeometryTests(unittest.TestCase):
    def test_every_edge_midpoint_maps_back_at_different_sizes(self):
        for size in (280, 560, 840):
            geometry = BoardGeometry(size)
            for move in all_moves():
                with self.subTest(size=size, move=move):
                    sx, sy, ex, ey = geometry.edge_points(move)
                    self.assertEqual(geometry.hit_test((sx + ex) / 2, (sy + ey) / 2), move)

    def test_margins_dots_and_nonfinite_coordinates_are_not_moves(self):
        geometry = BoardGeometry(560)
        for x, y in ((0, 560 / 12), (560 / 12, 0), (560, 280),
                     (280, 560), (-1, 100), (100, -1), (561, 100),
                     (float("nan"), 100), (100, float("inf"))):
            with self.subTest(x=x, y=y):
                self.assertIsNone(geometry.hit_test(x, y))
        for x in range(6):
            for y in range(6):
                self.assertIsNone(geometry.hit_test((x + 0.5) * geometry.spacing,
                                                   (y + 0.5) * geometry.spacing))


if __name__ == "__main__":
    unittest.main()
