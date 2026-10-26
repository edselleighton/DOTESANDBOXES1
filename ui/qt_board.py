"""Responsive, keyboard-operable presentation of the shared game state."""

from PySide6.QtCore import QEasingCurve, QPointF, QRectF, QSize, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from core.game_engine import Move
from ui.board_geometry import BoardGeometry
from ui.paper_style import BLUE, CORAL, INK
from ui.motion import CAPTURE_MS, LINE_MS

BOARD_BLUE = "#3589B8"
BOARD_CORAL = "#D6684C"


class GameBoard(QWidget):
    move_requested = Signal(object)
    selection_changed = Signal(str)
    feedback_changed = Signal()

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.input_enabled = False
        self._accepts_input = False
        self.motion_policy = None
        self.feedback = None
        self.feedback_elapsed = 0.0
        self.animation = QVariantAnimation(self)
        self.animation.valueChanged.connect(self._advance_feedback)
        self.animation.finished.connect(self.finish_feedback)
        self._easing = QEasingCurve(QEasingCurve.Type.OutCubic)
        self.paused = False
        self.stronger_contrast = False
        self.names = ("Player 1", "Player 2")
        self.selected = Move("row", (0, 0))
        self.hovered = None
        self.hint = None
        self.keyboard_selection = False
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(160, 160)
        self.setAccessibleName("Dots and Boxes board")
        self.setAccessibleDescription(
            "Six by six dots. Arrow keys select an edge; H or V changes orientation. "
            "Enter or Space draws the selected edge. Tab moves to match controls."
        )
        self._announce_selection()

    def sizeHint(self):
        return QSize(560, 560)

    def set_stronger_contrast(self, enabled):
        self.stronger_contrast = bool(enabled)
        self.update()

    def board_geometry(self):
        size = max(1, min(self.width(), self.height()) - 2)
        return BoardGeometry(size), QPointF((self.width() - size) / 2,
                                           (self.height() - size) / 2)

    def edge_center(self, move):
        geometry, offset = self.board_geometry()
        sx, sy, ex, ey = geometry.edge_points(move)
        return offset + QPointF((sx + ex) / 2, (sy + ey) / 2)

    def move_at(self, position):
        geometry, offset = self.board_geometry()
        point = position - offset
        return geometry.hit_test(point.x(), point.y())

    def refresh(self, accepts_input, paused, names):
        self._accepts_input = accepts_input
        self.input_enabled = accepts_input and not self.animating
        self.paused = paused
        self.names = names
        self.hovered = None
        self.hint = None
        self._announce_selection()
        self.update()

    @property
    def animating(self):
        return self.feedback is not None

    def set_motion_policy(self, policy):
        self.motion_policy = policy
        policy.changed.connect(self._motion_changed)
        self._motion_changed()

    def _motion_changed(self):
        if not self.motion_policy.enabled:
            self.finish_feedback()

    def animate_move(self, outcome):
        self.finish_feedback()
        if not self.motion_policy or not self.motion_policy.enabled or not self.isVisible():
            return
        self.feedback = outcome
        self.feedback_elapsed = 0.0
        self.input_enabled = False
        duration = CAPTURE_MS if outcome.captured_boxes else LINE_MS
        self.animation.setDuration(duration)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(float(duration))
        self.animation.start()
        self.feedback_changed.emit()

    def _advance_feedback(self, value):
        self.feedback_elapsed = float(value)
        self.update()

    def finish_feedback(self):
        was_animating = self.animating
        self.animation.stop()
        self.feedback = None
        self.input_enabled = self._accepts_input and not self.paused
        self.update()
        if was_animating:
            self.feedback_changed.emit()

    def hideEvent(self, event):
        self.finish_feedback()
        super().hideEvent(event)

    def show_hint(self, move):
        self.hint = move
        if move is not None:
            self.selected = move
            self.setFocus()
            self._announce_selection()
        self.update()

    def _announce_selection(self):
        x, y = self.selected.position
        orientation = "Horizontal" if self.selected.edge == "row" else "Vertical"
        state = "available" if self.engine.is_legal(self.selected) else "already drawn"
        text = f"{orientation} edge, column {x + 1}, row {y + 1}: {state}."
        self.setAccessibleName(f"Dots and Boxes board. {text}")
        self.selection_changed.emit(text)

    def mouseMoveEvent(self, event):
        move = self.move_at(event.position()) if self.input_enabled else None
        self.hovered = move if move is not None and self.engine.is_legal(move) else None
        self.setCursor(Qt.CursorShape.PointingHandCursor if self.hovered else Qt.CursorShape.ArrowCursor)
        self.update()

    def leaveEvent(self, event):
        self.hovered = None
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.input_enabled:
            move = self.move_at(event.position())
            if move is not None and self.engine.is_legal(move):
                self.selected = move
                self.keyboard_selection = False
                self.setFocus(Qt.FocusReason.MouseFocusReason)
                self.move_requested.emit(move)
                self._announce_selection()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self.keyboard_selection = True
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            if self.input_enabled:
                self.move_requested.emit(self.selected)
            event.accept()
            return
        x, y = self.selected.position
        edge = self.selected.edge
        if key == Qt.Key.Key_H:
            edge = "row"
        elif key == Qt.Key.Key_V:
            edge = "col"
        elif key == Qt.Key.Key_Left:
            x -= 1
        elif key == Qt.Key.Key_Right:
            x += 1
        elif key == Qt.Key.Key_Up:
            y -= 1
        elif key == Qt.Key.Key_Down:
            y += 1
        elif key == Qt.Key.Key_Home:
            x, y = 0, 0
        else:
            super().keyPressEvent(event)
            return
        self.selected = Move(edge, (max(0, min(x, 4 if edge == "row" else 5)),
                                    max(0, min(y, 5 if edge == "row" else 4))))
        self._announce_selection()
        self.update()
        event.accept()

    def focusInEvent(self, event):
        if event.reason() in (Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason):
            self.keyboard_selection = True
        self._announce_selection()
        self.update()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._announce_selection()
        self.update()
        super().focusOutEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        geometry, offset = self.board_geometry()
        painter.translate(offset)
        gap = geometry.spacing
        line_width = max(3, min(6, gap * .065))
        blue = "#1C5C88" if self.stronger_contrast else BOARD_BLUE
        coral = "#B63E2C" if self.stronger_contrast else BOARD_CORAL
        if self.stronger_contrast:
            line_width += 1.5

        def line(move, color, width=line_width, style=Qt.PenStyle.SolidLine, progress=1.0):
            sx, sy, ex, ey = geometry.edge_points(move)
            painter.setPen(QPen(QColor(color), width, style, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(sx, sy), QPointF(sx + (ex - sx) * progress,
                                                     sy + (ey - sy) * progress))

        # Ownership uses initials as well as color, including identical names.
        initials = [name.strip()[0].upper() for name in self.names]
        if initials[0] == initials[1]:
            initials = ["1", "2"]
        font = QFont(self.font())
        font.setPixelSize(max(11, int(gap * .23)))
        font.setBold(True)
        painter.setFont(font)
        for x in range(5):
            for y in range(5):
                owner = int(self.engine.box_owner[x, y])
                if owner:
                    if self.feedback and (x, y) in self.feedback.captured_boxes:
                        painter.setOpacity(self._easing.valueForProgress(
                            min(1.0, self.feedback_elapsed / CAPTURE_MS)))
                    rect = QRectF((x + .5) * gap, (y + .5) * gap, gap, gap)
                    painter.fillRect(rect, QColor("#CBE3EF" if owner == 1 else "#F7D3C1"))
                    painter.setPen(QColor(BLUE if owner == 1 else CORAL))
                    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, initials[owner - 1])
                    painter.setOpacity(1.0)
        for x in range(6):
            for y in range(6):
                if x < 5:
                    line(Move("row", (x, y)), "#827765" if self.stronger_contrast else "#D2C6AE",
                         1.8 if self.stronger_contrast else 1.2)
                if y < 5:
                    line(Move("col", (x, y)), "#827765" if self.stronger_contrast else "#D2C6AE",
                         1.8 if self.stronger_contrast else 1.2)
        for outcome in self.engine.history:
            progress = (self._easing.valueForProgress(min(1.0, self.feedback_elapsed / LINE_MS))
                        if outcome is self.feedback else 1.0)
            line(outcome.move, blue if outcome.player == 1 else coral, line_width, progress=progress)

        preview = self.hovered or (self.selected if self.hasFocus() and self.keyboard_selection else None)
        if self.input_enabled and preview and self.engine.is_legal(preview):
            line(preview, blue if self.engine.current_player == 1 else coral,
                 line_width, Qt.PenStyle.DashLine)
        if self.hint is not None and self.engine.is_legal(self.hint):
            line(self.hint, "#9B681E", line_width + 2, Qt.PenStyle.DotLine)

        radius = max(3.5, min(6, gap * .075))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(INK))
        for x in range(6):
            for y in range(6):
                painter.drawEllipse(QPointF((x + .5) * gap, (y + .5) * gap), radius, radius)

        if self.engine.history:
            latest = self.engine.history[-1]
            sx, sy, ex, ey = geometry.edge_points(latest.move)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(blue if latest.player == 1 else coral), 2.5))
            for point in (QPointF(sx, sy), QPointF(ex, ey)):
                painter.drawEllipse(point, radius + 3, radius + 3)
            painter.setPen(QPen(QColor("#EAA331"), 2.4,
                                Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            anchor = QPointF((sx + ex) / 2, (sy + ey) / 2)
            if latest.move.edge == "row":
                anchor += QPointF(0, -13)
            else:
                anchor += QPointF(13, 0)
            painter.drawLine(anchor + QPointF(-6, -3), anchor + QPointF(-9, -8))
            painter.drawLine(anchor + QPointF(1, -5), anchor + QPointF(1, -11))
            painter.drawLine(anchor + QPointF(7, -3), anchor + QPointF(11, -7))

        if self.hasFocus() and self.keyboard_selection and not self.paused:
            painter.setPen(QPen(QColor(BLUE), 1.5, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            sx, sy, ex, ey = geometry.edge_points(self.selected)
            painter.drawRoundedRect(QRectF(QPointF(sx, sy), QPointF(ex, ey))
                                    .normalized().adjusted(-8, -8, 8, 8), 8, 8)

        if self.paused:
            painter.fillRect(QRectF(0, 0, geometry.size, geometry.size), QColor(255, 249, 236, 235))
            painter.setPen(QColor(INK))
            font.setPixelSize(max(18, min(36, int(geometry.size / 12))))
            painter.setFont(font)
            painter.drawText(QRectF(12, 12, geometry.size - 24, geometry.size - 24),
                             Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                             "A little break.\nResume when\nyou’re ready.")
