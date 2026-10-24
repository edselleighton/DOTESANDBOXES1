"""Small, interruptible press feedback around native Qt button behavior."""

from PySide6.QtCore import QEasingCurve, QEvent, QVariantAnimation
from PySide6.QtWidgets import QPushButton, QStyle, QStyleOptionButton, QStylePainter


class MotionButton(QPushButton):
    """Keep native interaction and styling while gently pressing into the paper.

    Motion is opt-in: the owning window supplies a policy with ``enabled`` and a
    ``changed`` signal. Hit testing, layout, focus and accessibility stay native.
    """

    FEEDBACK_DURATION_MS = 120
    PRESSED_SCALE = 0.98

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._policy = None
        self._feedback_scale = 1.0
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(self.FEEDBACK_DURATION_MS)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.valueChanged.connect(self._set_feedback_scale)
        self.pressed.connect(self._press_feedback)
        self.released.connect(self._release_feedback)

    @property
    def feedback_scale(self):
        return self._feedback_scale

    @property
    def animation(self):
        return self._animation

    def set_motion_policy(self, policy):
        if self._policy is policy:
            return
        if self._policy is not None:
            self._policy.changed.disconnect(self._policy_changed)
        self._policy = policy
        if policy is not None:
            policy.changed.connect(self._policy_changed)
        self._reset_feedback()

    def _motion_enabled(self):
        return (self._policy is not None and self._policy.enabled
                and self.isEnabled() and self.isVisible()
                and not self.window().isMinimized())

    def _policy_changed(self, *args):
        if not self._motion_enabled():
            self._reset_feedback()

    def _set_feedback_scale(self, value):
        self._feedback_scale = float(value)
        self.update()

    def _animate_to(self, target):
        self._animation.stop()
        self._animation.setStartValue(self._feedback_scale)
        self._animation.setEndValue(target)
        self._animation.start()

    def _press_feedback(self):
        if self._motion_enabled():
            self._animate_to(self.PRESSED_SCALE)

    def _release_feedback(self):
        if not self._motion_enabled():
            self._reset_feedback()
            return
        # Native click() emits press and release synchronously. Give these quick
        # activations the same small release feedback without emitting a click.
        if self._feedback_scale == 1.0:
            self._set_feedback_scale(self.PRESSED_SCALE)
        self._animate_to(1.0)

    def _reset_feedback(self):
        self._animation.stop()
        self._set_feedback_scale(1.0)

    def hideEvent(self, event):
        self._reset_feedback()
        super().hideEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.EnabledChange and not self.isEnabled():
            self._reset_feedback()
        elif event.type() == QEvent.Type.WindowStateChange and self.window().isMinimized():
            self._reset_feedback()
        super().changeEvent(event)

    def paintEvent(self, event):
        if self._feedback_scale == 1.0:
            super().paintEvent(event)
            return
        painter = QStylePainter(self)
        option = QStyleOptionButton()
        self.initStyleOption(option)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._feedback_scale, self._feedback_scale)
        painter.translate(-self.width() / 2, -self.height() / 2)
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)
