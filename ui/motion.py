"""Shared, interruptible motion policy and short page transitions."""

import ctypes
import sys

from PySide6.QtCore import QEasingCurve, QObject, QVariantAnimation, Signal
from PySide6.QtWidgets import QGraphicsOpacityEffect, QStackedWidget

CONTROL_MS = 120
LINE_MS = 160
CAPTURE_MS = 220
PAGE_MS = 180
AI_MOVE_MS = 300


def system_reduced_motion():
    """Read Windows' client-area animation preference without changing it."""
    if sys.platform != "win32":
        return False
    try:
        enabled = ctypes.c_int(1)
        # SPI_GETCLIENTAREAANIMATION, documented by Microsoft for a BOOL pointer.
        if ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(enabled), 0):
            return not bool(enabled.value)
    except (AttributeError, OSError):
        pass
    return False


class MotionPolicy(QObject):
    changed = Signal()

    def __init__(self, reduced_motion=False, parent=None):
        super().__init__(parent)
        self.reduced_motion = reduced_motion
        self.suspended = False

    @property
    def enabled(self):
        return not self.reduced_motion and not self.suspended

    def set_reduced_motion(self, enabled):
        if self.reduced_motion != enabled:
            self.reduced_motion = enabled
            self.changed.emit()

    def set_suspended(self, suspended):
        if self.suspended != suspended:
            self.suspended = suspended
            self.changed.emit()


class PageStack(QStackedWidget):
    """Fade the new page; its real controls stay responsive during navigation."""
    def __init__(self, policy, parent=None):
        super().__init__(parent)
        self.policy = policy
        self._transition_widget = None
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(PAGE_MS)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.setStartValue(.35)
        self.animation.setEndValue(1.0)
        self.animation.valueChanged.connect(self._set_opacity)
        self.animation.finished.connect(self.finish_transition)
        policy.changed.connect(self._policy_changed)

    def setCurrentWidget(self, widget):
        if widget is self.currentWidget():
            return
        self.finish_transition()
        super().setCurrentWidget(widget)
        if self.currentWidget() is widget and self.policy.enabled and self.isVisible():
            self._transition_widget = widget
            effect = QGraphicsOpacityEffect(widget)
            effect.setOpacity(.35)
            widget.setGraphicsEffect(effect)
            self.animation.start()

    def _set_opacity(self, value):
        if self._transition_widget is not None:
            effect = self._transition_widget.graphicsEffect()
            if effect is not None:
                effect.setOpacity(float(value))

    def finish_transition(self):
        self.animation.stop()
        if self._transition_widget is not None:
            self._transition_widget.setGraphicsEffect(None)
            self._transition_widget = None

    def _policy_changed(self):
        if not self.policy.enabled:
            self.finish_transition()

    def resizeEvent(self, event):
        self.finish_transition()
        super().resizeEvent(event)

    def hideEvent(self, event):
        self.finish_transition()
        super().hideEvent(event)
