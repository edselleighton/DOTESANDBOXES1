"""Native button input remains immediate while optional feedback is bounded."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QAbstractAnimation, QObject, Qt, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from ui.motion_controls import MotionButton


class MotionPolicyStub(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.enabled = True

    def disable(self):
        self.enabled = False
        self.changed.emit()


class MotionControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.button = MotionButton("Play a round")
        self.button.resize(200, 48)
        self.button.setAccessibleName("Play a round")
        self.button.show()
        self.app.processEvents()
        self.addCleanup(self.button.close)
        self.policy = MotionPolicyStub()
        self.activations = []
        self.button.clicked.connect(lambda checked=False: self.activations.append(checked))

    def enable_motion(self):
        self.button.set_motion_policy(self.policy)

    def test_default_static_button_preserves_activation_and_accessible_name(self):
        self.button.click()
        self.assertEqual(self.activations, [False])
        self.assertEqual(self.button.feedback_scale, 1.0)
        self.assertEqual(self.button.animation.state(), QAbstractAnimation.State.Stopped)
        self.assertEqual(self.button.accessibleName(), "Play a round")

    def test_mouse_feedback_never_moves_the_hit_rectangle_or_duplicates_activation(self):
        self.enable_motion()
        bounds = self.button.geometry()
        QTest.mousePress(self.button, Qt.MouseButton.LeftButton)
        self.button.animation.setCurrentTime(60)
        self.assertGreater(self.button.feedback_scale, self.button.PRESSED_SCALE)
        self.assertLess(self.button.feedback_scale, 1.0)
        self.assertEqual(self.activations, [])
        self.assertEqual(self.button.geometry(), bounds)
        QTest.mouseRelease(self.button, Qt.MouseButton.LeftButton)
        self.assertEqual(self.activations, [False])
        self.button.animation.setCurrentTime(120)
        self.assertEqual(self.button.feedback_scale, 1.0)
        self.assertEqual(self.button.animation.state(), QAbstractAnimation.State.Stopped)
        self.assertEqual(self.button.geometry(), bounds)

    def test_keyboard_and_programmatic_clicks_use_native_single_activation(self):
        self.enable_motion()
        self.button.setFocus()
        QTest.keyClick(self.button, Qt.Key.Key_Space)
        self.assertEqual(self.activations, [False])
        self.assertLess(self.button.feedback_scale, 1.0)
        self.button.animation.setCurrentTime(120)
        self.button.click()
        self.assertEqual(self.activations, [False, False])
        self.assertLess(self.button.feedback_scale, 1.0)
        self.assertEqual(self.button.animation.duration(), 120)

    def test_repeated_press_reverses_from_current_feedback(self):
        self.enable_motion()
        QTest.mousePress(self.button, Qt.MouseButton.LeftButton)
        self.button.animation.setCurrentTime(80)
        QTest.mouseRelease(self.button, Qt.MouseButton.LeftButton)
        self.button.animation.setCurrentTime(40)
        scale = self.button.feedback_scale
        QTest.mousePress(self.button, Qt.MouseButton.LeftButton)
        self.assertAlmostEqual(self.button.feedback_scale, scale)
        self.button.animation.setCurrentTime(120)
        self.assertAlmostEqual(self.button.feedback_scale, 0.98)
        QTest.mouseRelease(self.button, Qt.MouseButton.LeftButton)
        self.assertEqual(len(self.activations), 2)

    def test_disabling_motion_immediately_restores_static_native_feedback(self):
        self.enable_motion()
        QTest.mousePress(self.button, Qt.MouseButton.LeftButton)
        self.button.animation.setCurrentTime(60)
        self.policy.disable()
        self.assertEqual(self.button.feedback_scale, 1.0)
        self.assertEqual(self.button.animation.state(), QAbstractAnimation.State.Stopped)
        self.assertTrue(self.button.isDown())
        QTest.mouseRelease(self.button, Qt.MouseButton.LeftButton)
        self.assertEqual(self.activations, [False])
        self.assertEqual(self.button.feedback_scale, 1.0)

    def test_hide_disable_and_policy_replacement_cancel_feedback(self):
        self.enable_motion()
        for cancel in (self.button.hide, lambda: self.button.setEnabled(False),
                       lambda: self.button.set_motion_policy(None)):
            self.button.show()
            self.button.setEnabled(True)
            self.button.set_motion_policy(self.policy)
            self.button.click()
            self.assertLess(self.button.feedback_scale, 1.0)
            cancel()
            self.assertEqual(self.button.feedback_scale, 1.0)
            self.assertEqual(self.button.animation.state(), QAbstractAnimation.State.Stopped)

    def test_minimized_button_stops_feedback_and_checked_state_stays_native(self):
        self.enable_motion()
        self.button.setCheckable(True)
        self.button.click()
        self.assertTrue(self.button.isChecked())
        self.assertEqual(self.activations, [True])
        self.button.showMinimized()
        self.app.processEvents()
        self.assertEqual(self.button.feedback_scale, 1.0)
        self.assertEqual(self.button.animation.state(), QAbstractAnimation.State.Stopped)
        self.button.showNormal()
        self.app.processEvents()
        self.button.click()
        self.assertFalse(self.button.isChecked())
        self.assertEqual(self.activations, [True, False])


if __name__ == "__main__":
    unittest.main()
