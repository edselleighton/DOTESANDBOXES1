import unittest
from unittest.mock import patch

from core.game_engine import GameEngine, MatchConfig, Move
from core.match_controller import MatchController
from test_game_engine import all_moves


class Scheduler:
    def __init__(self):
        self.jobs = {}
        self.callbacks = {}
        self.sequence = 0

    def schedule(self, delay, callback):
        self.sequence += 1
        self.jobs[self.sequence] = callback
        self.callbacks[self.sequence] = callback
        return self.sequence

    def cancel(self, handle):
        del self.jobs[handle]

    def run_next(self):
        handle = min(self.jobs)
        self.jobs.pop(handle)()


class TurnSequencingTests(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine()
        self.scheduler = Scheduler()
        self.changes = []
        self.finishes = []
        self.controller = MatchController(
            self.engine, self.scheduler.schedule, self.scheduler.cancel,
            self.changes.append, self.finishes.append,
        )

    def test_human_cannot_play_or_request_hint_during_ai_delay(self):
        self.controller.start(MatchConfig(mode="AI", difficulty="easy"))
        self.controller.play_human(Move("row", (0, 0)))
        self.assertFalse(self.controller.accepts_human_move)
        self.assertIsNone(self.controller.play_human(Move("row", (1, 0))))
        self.assertIsNone(self.controller.get_hint())
        self.assertFalse(self.controller.undo_move())
        self.assertEqual(len(self.engine.history), 1)
        self.assertEqual(len(self.scheduler.jobs), 1)
        self.scheduler.run_next()
        self.assertEqual(len(self.engine.history), 2)
        self.assertTrue(self.controller.accepts_human_move)
        self.assertFalse(self.scheduler.jobs)

    def test_stale_callback_cannot_mutate_or_clear_a_new_match(self):
        config = MatchConfig(mode="AI", difficulty="easy")
        self.controller.start(config)
        self.controller.play_human(Move("row", (0, 0)))
        stale = next(iter(self.scheduler.callbacks.values()))
        self.controller.start(config)
        self.controller.play_human(Move("row", (1, 0)))
        pending = dict(self.scheduler.jobs)
        stale()
        self.assertEqual(len(self.engine.history), 1)
        self.assertEqual(self.scheduler.jobs, pending)
        self.scheduler.run_next()
        self.assertEqual(len(self.engine.history), 2)

    def test_leaving_a_match_cancels_computer_work(self):
        self.controller.start(MatchConfig(mode="AI"))
        self.controller.play_human(Move("row", (0, 0)))
        callback = next(iter(self.scheduler.callbacks.values()))
        self.controller.stop()
        self.assertFalse(self.scheduler.jobs)
        callback()
        self.assertEqual(len(self.engine.history), 1)
        self.assertIsNone(self.controller.play_human(Move("row", (1, 0))))

    def test_complete_ai_matches_finish_once_without_pending_callbacks(self):
        for difficulty in ("easy", "medium", "hard"):
            with self.subTest(difficulty=difficulty):
                self.finishes.clear()
                self.controller.start(MatchConfig(mode="AI", difficulty=difficulty))
                for _ in range(120):
                    if not self.controller.active:
                        break
                    if self.controller.accepts_human_move:
                        move = next(move for move in all_moves() if self.engine.is_legal(move))
                        self.controller.play_human(move)
                    else:
                        self.assertEqual(len(self.scheduler.jobs), 1)
                        self.scheduler.run_next()
                    self.assertLessEqual(len(self.scheduler.jobs), 1)
                self.assertFalse(self.controller.active)
                self.assertEqual(len(self.finishes), 1)
                self.assertEqual(len(self.engine.history), 60)
                self.assertEqual(sum(self.engine.scores), 25)
                self.assertFalse(self.scheduler.jobs)
                self.assertIsNone(self.controller.play_human(Move("row", (0, 0))))
                self.assertEqual(len(self.finishes), 1)

    def test_computer_captures_are_scheduled_one_move_at_a_time(self):
        self.controller.start(MatchConfig(mode="AI", difficulty="medium"))
        self.controller.play_human(Move("row", (0, 0)))
        with patch.object(self.engine.ai, "easy_move", return_value=("col", (0, 0))):
            self.scheduler.run_next()
        self.controller.play_human(Move("row", (0, 1)))
        self.scheduler.run_next()
        self.assertEqual(self.engine.scores, (0, 1))
        self.assertEqual(self.engine.current_player, 2)
        self.assertEqual(len(self.scheduler.jobs), 1)
        self.assertEqual(len(self.engine.history), 4)
        self.scheduler.run_next()
        self.assertTrue(self.controller.accepts_human_move)

    def test_reset_from_a_view_callback_does_not_finish_the_new_match(self):
        def on_move(outcome):
            if outcome is not None and outcome.finished:
                controller.start(MatchConfig())

        controller = MatchController(
            self.engine, self.scheduler.schedule, self.scheduler.cancel,
            on_move, self.finishes.append,
        )
        controller.start(MatchConfig())
        for move in all_moves():
            controller.play_human(move)
        self.assertTrue(controller.active)
        self.assertEqual(self.engine.history, ())
        self.assertEqual(self.finishes, [])

    def test_local_non_scoring_move_can_be_undone(self):
        self.controller.start(MatchConfig())
        self.controller.play_human(Move("row", (0, 0)))
        self.assertTrue(self.controller.can_undo)
        self.assertTrue(self.controller.undo_move())
        self.assertFalse(self.controller.can_undo)
        self.assertEqual(self.engine.current_player, 1)
        self.assertFalse(self.scheduler.jobs)


if __name__ == "__main__":
    unittest.main()
