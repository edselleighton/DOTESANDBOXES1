"""Paper Club match composition, native controls and Qt timer ownership."""

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QSizePolicy, QStyle, QStyleOptionButton, QStylePainter,
    QVBoxLayout, QWidget,
)

from core.game_engine import GameEngine, Move
from core.match_controller import MatchController
from ui.paper_style import BLUE, CORAL, INK, PaperSurface, button, label
from ui.qt_board import GameBoard
from ui.motion import AI_MOVE_MS
from ui.motion_controls import MotionButton
from ui.paper_art import PaperLogo, paper_icon


class Avatar(QWidget):
    def __init__(self, color):
        super().__init__()
        self.color = color
        self.setFixedSize(64, 64)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(self.width() / 56, self.height() / 56)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(55, 41, 20, 22))
        painter.drawEllipse(QRectF(3, 5, 50, 50))
        painter.setBrush(QColor(self.color))
        painter.drawEllipse(QRectF(2, 2, 50, 50))
        painter.setBrush(QColor("#FFF9EC"))
        painter.drawEllipse(QRectF(20, 12, 14, 14))
        path = QPainterPath()
        path.moveTo(13, 42)
        path.cubicTo(13, 25, 41, 25, 41, 42)
        path.closeSubpath()
        painter.drawPath(path)


class TurnBanner(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setMinimumHeight(74)
        self.setObjectName("turnBanner")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(27, 13, -27, -13)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#BDCAA8"))
        path = QPainterPath()
        path.moveTo(rect.left() + 8, rect.top() + 2)
        path.lineTo(rect.right() - 8, rect.top() - 2)
        path.lineTo(rect.right(), rect.top() + 4)
        path.lineTo(rect.right() - 5, rect.top() + 10)
        path.lineTo(rect.right() + 3, rect.top() + 18)
        path.lineTo(rect.right() - 4, rect.center().y() + 4)
        path.lineTo(rect.right() + 1, rect.bottom() - 6)
        path.lineTo(rect.right() - 7, rect.bottom())
        path.lineTo(rect.left() + 3, rect.bottom() + 3)
        path.lineTo(rect.left() - 3, rect.bottom() - 5)
        path.lineTo(rect.left() + 3, rect.bottom() - 12)
        path.lineTo(rect.left() - 4, rect.center().y())
        path.lineTo(rect.left() + 3, rect.top() + 12)
        path.lineTo(rect.left() - 1, rect.top() + 7)
        path.closeSubpath()
        painter.drawPath(path)
        painter.setPen(QPen(QColor("#EAA331"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for left in (True, False):
            x = 13 if left else self.width() - 13
            for y, dy in ((25, -3), (37, 0), (49, 3)):
                painter.drawLine(QPointF(x - 3, y), QPointF(x + 3, y + dy if left else y - dy))
        font = QFont(self.font())
        font.setFamily("Fredoka")
        font.setWeight(QFont.Weight.DemiBold)
        base_size = max(25, min(40, int(self.width() * .073)))
        font.setPixelSize(base_size if len(self.text()) < 21 else int(base_size * .82))
        painter.setFont(font)
        painter.setPen(QColor(INK))
        painter.drawText(rect.adjusted(4, 0, -4, 0),
                         Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.text())


class BoxCounter(QLabel):
    """A visual one-box count with native readable text for accessibility."""
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(72)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#D9CDB9"), 1))
        painter.drawLine(0, 1, self.width(), 1)
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        box_side = max(28, min(42, self.height() * .36))
        box = QRectF(8, (self.height() - box_side) / 2, box_side, box_side)
        painter.setPen(QPen(QColor("#BFB7A8"), 1.4))
        painter.drawRect(box)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(INK))
        for point in (box.topLeft(), box.topRight(), box.bottomLeft(), box.bottomRight()):
            painter.drawEllipse(point, 2.5, 2.5)
        painter.setPen(QColor(INK))
        font = QFont(self.font())
        font.setPixelSize(max(18, min(28, int(self.width() * .052))))
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        painter.drawText(QRectF(box_side + 35, 0, self.width() - box_side - 35, self.height()),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())


class BoardCaption(QLabel):
    def paintEvent(self, event):
        super().paintEvent(event)
        text_width = min(self.fontMetrics().horizontalAdvance(self.text()), self.width() - 64)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#EAA331"), 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for side in (-1, 1):
            x = self.width() / 2 + side * (text_width / 2 + 16)
            y = self.height() / 2 - 2
            painter.drawLine(QPointF(x, y - 6), QPointF(x + side * 5, y - 9))
            painter.drawLine(QPointF(x + side * 2, y), QPointF(x + side * 8, y))
            painter.drawLine(QPointF(x, y + 6), QPointF(x + side * 5, y + 9))


class PlayerName(QLabel):
    """Keep the score visible while preserving a long name for assistive tools."""
    def __init__(self, role):
        super().__init__()
        self.full_text = ""
        self.setObjectName(role)
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def set_name(self, text):
        self.full_text = text
        self.setToolTip(text)
        self.setAccessibleName(text)
        self.setText(self.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight, self.width()))

    def resizeEvent(self, event):
        self.set_name(self.full_text)
        super().resizeEvent(event)


class PlayerRow(QWidget):
    def __init__(self, color, role, compact=False):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(14)
        self.avatar = Avatar(color)
        self.name = PlayerName(role)
        self.name.setStyleSheet("font-size: 18px; font-weight: 700;")
        self.score = label("0", "matchScore")
        self.score.setStyleSheet(f"color: {color}; font-size: 52px; font-weight: 600;")
        self.score.setFixedWidth(66)
        self.score.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.layout.addWidget(self.avatar)
        self.layout.addWidget(self.name, 1)
        self.layout.addWidget(self.score)
        if compact:
            self.avatar.hide()
            self.name.setStyleSheet("font-size: 14px; font-weight: 600;")
            self.score.setStyleSheet(f"color: {color}; font-size: 22px;")
            self.score.setFixedWidth(32)
            self.layout.setContentsMargins(0, 0, 0, 0)
            self.layout.setSpacing(4)

    def refresh(self, name, score, active):
        self.name.set_name(name)
        self.score.setText(str(score))
        self.name.setAccessibleName(f"{name}{', current player' if active else ''}")
        self.score.setAccessibleName(f"{name}: {score} boxes")


class MatchActionButton(MotionButton):
    """Native button behavior with the mockup's icon-over-caption composition."""
    def __init__(self, text, kind, primary=False, compact=False):
        super().__init__(text)
        self.kind = kind
        self.primary = primary
        self.compact = compact
        self.setObjectName("primary" if primary else "")
        self.setMinimumWidth(64)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        height = 60 if compact else 94
        self.setStyleSheet(f"QPushButton {{ padding: 0; border-radius: 9px; min-height: {height}px; }}")
        self.setFixedHeight(height)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.text = ""
        option.icon = QIcon()
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self.feedback_scale, self.feedback_scale)
        painter.translate(-self.width() / 2, -self.height() / 2)
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)
        color = "#8E8D81" if not self.isEnabled() else ("#FFF9EC" if self.primary else INK)
        kind = "play" if self.text() == "Resume" else self.kind
        icon_size = 20 if self.compact else max(26, int(self.height() * .28))
        icon_top = 8 if self.compact else int(self.height() * .16)
        icon = paper_icon(kind, color, icon_size)
        icon.paint(painter, (self.width() - icon_size) // 2, icon_top, icon_size, icon_size)
        font = QFont(self.font())
        font.setPixelSize(13 if self.compact else max(16, int(self.height() * .17)))
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(QColor(color))
        painter.drawText(QRectF(3, icon_top + icon_size + 3, self.width() - 6,
                               self.height() - icon_top - icon_size - 7),
                         Qt.AlignmentFlag.AlignCenter, self.text())


class MatchActions(QWidget):
    def __init__(self, compact=False):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.hint = MatchActionButton("Hint", "hint", True, compact)
        self.undo = MatchActionButton("Undo", "undo", compact=compact)
        self.pause = MatchActionButton("Pause", "pause", compact=compact)
        for control in (self.hint, self.undo, self.pause):
            layout.addWidget(control, 1)


class MatchStage(QWidget):
    """Keep paper sheets aligned and bound board size by both available axes."""
    sidebar_resized = Signal(int)
    def __init__(self, board_sheet, sidebar, header):
        super().__init__()
        self.board_sheet = board_sheet
        self.sidebar = sidebar
        self.header = header
        self.backing = PaperSurface(self)
        self.backing.lower()
        board_sheet.setParent(self)
        sidebar.setParent(self)
        header.setParent(self)
        self.compact = False
        self.setMinimumSize(200, 200)

    def arrange(self):
        height = max(1, self.height())
        if self.compact:
            self.backing.hide()
            side = min(self.width(), height)
            self.board_sheet.setGeometry((self.width() - side) // 2, 0, side, side)
        else:
            self.backing.show()
            board_side = max(1, int(min(980, (height - 22) / 1.10, (self.width() - 42) / 1.68)))
            sidebar_width = int(board_side * .68)
            width = board_side + sidebar_width + 6
            left = (self.width() - width) // 2
            header_height = max(48, round(board_side * .085))
            top = max(0, (height - board_side - header_height - 18) // 2)
            self.backing.setGeometry(left - 13, top, width + 26, board_side + header_height + 25)
            self.header.setGeometry(left + 12, top + 8, width - 24, header_height)
            self.board_sheet.setGeometry(left, top + header_height + 9, board_side, board_side)
            self.sidebar.setGeometry(left + board_side + 6, top + header_height + 9, sidebar_width, board_side)
            self.sidebar_resized.emit(board_side)

    def resizeEvent(self, event):
        self.arrange()
        super().resizeEvent(event)


class MatchPage(QWidget):
    sound_requested = Signal(str)
    home_requested = Signal()
    new_match_requested = Signal()
    pause_requested = Signal()

    def __init__(self):
        super().__init__()
        self.engine = GameEngine()
        self.motion_policy = None
        self._explanation = ""
        self._ai_error = ""
        self.timers = set()
        self.controller = MatchController(self.engine, self._schedule, self._cancel,
                                          self._on_move, self._on_finished)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(8)
        self.header = QWidget()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(22)
        self.title = PaperLogo()
        self.title.setMinimumWidth(270)
        self.title.setMaximumWidth(660)
        self.mode_label = label("", "fieldLabel")
        self.mode_label.setStyleSheet("font-size: 15px; font-weight: 600; border-left: 1px solid #D7CCB7; padding-left: 20px;")
        self.home_button = button("Home", "quiet")
        self.home_button.setParent(self)
        self.home_button.hide()
        self.home_button.clicked.connect(self.home_requested)
        header_layout.addWidget(self.title, 5)
        header_layout.addWidget(self.mode_label, 6)

        self.compact_strip = PaperSurface()
        strip_layout = QHBoxLayout(self.compact_strip)
        strip_layout.setContentsMargins(20, 8, 20, 16)
        strip_layout.setSpacing(16)
        self.compact_players = (PlayerRow(BLUE, "blueLabel", True),
                                PlayerRow(CORAL, "coralLabel", True))
        self.compact_turn = label("", "fieldLabel")
        self.compact_turn.setTextFormat(Qt.TextFormat.PlainText)
        self.compact_turn.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        for player in self.compact_players:
            strip_layout.addWidget(player, 1)
        strip_layout.addWidget(self.compact_turn, 2)
        self.root_layout.addWidget(self.compact_strip)

        self.board_sheet = PaperSurface()
        board_layout = QVBoxLayout(self.board_sheet)
        board_layout.setContentsMargins(9, 7, 11, 23)
        board_layout.setSpacing(0)
        self.board = GameBoard(self.engine)
        self.board.move_requested.connect(self.play_human)
        board_layout.addWidget(self.board, 1)
        self.caption = BoardCaption("Complete a box. Play again.")
        self.caption.setObjectName("boardCaption")
        self.caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        board_layout.addWidget(self.caption)
        self.sidebar = PaperSurface()
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(27, 14, 29, 30)
        side_layout.setSpacing(10)
        self.turn_banner = TurnBanner()
        self.turn_banner.setTextFormat(Qt.TextFormat.PlainText)
        side_layout.addWidget(self.turn_banner, 1)
        self.players = (PlayerRow(BLUE, "blueLabel"), PlayerRow(CORAL, "coralLabel"))
        for player in self.players:
            player.setMinimumHeight(66)
            side_layout.addWidget(player, 1)
        self.remaining = BoxCounter()
        side_layout.addWidget(self.remaining, 1)
        self.action_explanation = label("", "secondary")
        self.action_explanation.hide()
        side_layout.addWidget(self.action_explanation)
        self.actions = MatchActions()
        side_layout.addWidget(self.actions)

        self.result_group = QWidget()
        self.result_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        result_group_layout = QVBoxLayout(self.result_group)
        result_group_layout.setContentsMargins(0, 0, 0, 0)
        result_group_layout.setSpacing(10)
        self.result_banner = TurnBanner()
        self.result_banner.setFixedHeight(86)
        self.result_banner.setTextFormat(Qt.TextFormat.PlainText)
        result_group_layout.addWidget(self.result_banner)
        self.result_summary = label("", "heading")
        self.result_summary.setFixedHeight(88)
        self.result_summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_summary.setTextFormat(Qt.TextFormat.RichText)
        result_group_layout.addWidget(self.result_summary)
        self.result_names = label("", "secondary")
        self.result_names.setTextFormat(Qt.TextFormat.PlainText)
        self.result_names.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_names.setWordWrap(True)
        self.result_names.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.result_names.setMinimumHeight(28)
        result_group_layout.addWidget(self.result_names)
        result_group_layout.addSpacing(14)
        self.rematch_button = button("Rematch", "primary")
        self.rematch_button.setIcon(paper_icon("undo", "#FFF9EC"))
        self.rematch_button.clicked.connect(self.rematch)
        result_group_layout.addWidget(self.rematch_button)
        self.new_button = button("New game")
        self.new_button.setIcon(paper_icon("play"))
        self.new_button.clicked.connect(self.new_match_requested)
        result_group_layout.addWidget(self.new_button)
        self.result_home = button("Home", "quiet")
        self.result_home.setIcon(paper_icon("home"))
        self.result_home.clicked.connect(self.home_requested)
        result_group_layout.addWidget(self.result_home)
        self.result_group.hide()
        side_layout.addWidget(self.result_group, 1, Qt.AlignmentFlag.AlignVCenter)
        self.stage = MatchStage(self.board_sheet, self.sidebar, self.header)
        self._sidebar_scale = 0
        self.stage.sidebar_resized.connect(self._scale_sidebar)
        self.root_layout.addWidget(self.stage, 1)

        self.compact_actions = MatchActions(compact=True)
        self.compact_home = button("Home", "quiet")
        self.compact_home.setParent(self)
        self.compact_home.hide()
        self.compact_home.clicked.connect(self.home_requested)
        self.root_layout.addWidget(self.compact_actions)
        self.compact_results = QWidget()
        result_layout = QHBoxLayout(self.compact_results)
        result_layout.setContentsMargins(0, 0, 0, 0)
        self.compact_rematch = button("Rematch", "primary")
        self.compact_rematch.clicked.connect(self.rematch)
        result_layout.addWidget(self.compact_rematch)
        self.compact_new = button("New game")
        self.compact_new.clicked.connect(self.new_match_requested)
        result_layout.addWidget(self.compact_new)
        self.compact_result_home = button("Home", "quiet")
        self.compact_result_home.clicked.connect(self.home_requested)
        result_layout.addWidget(self.compact_result_home)
        self.compact_results.hide()
        self.root_layout.addWidget(self.compact_results)
        self.compact_explanation = label("", "secondary")
        self.compact_explanation.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.compact_explanation.hide()
        self.root_layout.addWidget(self.compact_explanation)
        self._keyboard_instructions = "Arrows: select · H / V: direction · Enter: draw · Tab: controls"
        self.keyboard_help = label(self._keyboard_instructions, "secondary")
        self.keyboard_help.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.keyboard_help.hide()
        self.root_layout.addWidget(self.keyboard_help)
        self.board.selection_changed.connect(self._selection_changed)
        self.board.setToolTip(self.board.accessibleDescription())
        for actions in (self.actions, self.compact_actions):
            actions.hint.clicked.connect(self.show_hint)
            actions.undo.clicked.connect(self.undo)
            actions.pause.clicked.connect(self.toggle_pause)
        QWidget.setTabOrder(self.board, self.actions.hint)
        QWidget.setTabOrder(self.actions.hint, self.actions.undo)
        QWidget.setTabOrder(self.actions.undo, self.actions.pause)
        QWidget.setTabOrder(self.actions.pause, self.rematch_button)
        QWidget.setTabOrder(self.rematch_button, self.new_button)
        QWidget.setTabOrder(self.new_button, self.compact_actions.hint)
        QWidget.setTabOrder(self.compact_actions.hint, self.compact_actions.undo)
        QWidget.setTabOrder(self.compact_actions.undo, self.compact_actions.pause)
        QWidget.setTabOrder(self.compact_actions.pause, self.compact_rematch)
        self.board.feedback_changed.connect(self._sync_motion_input)

    def set_motion_policy(self, policy):
        self.motion_policy = policy
        self.board.set_motion_policy(policy)

    def _scale_sidebar(self, height):
        if self._sidebar_scale == height:
            return
        self._sidebar_scale = height
        avatar_size = max(56, min(112, round(height * .12)))
        name_size = max(16, min(26, round(height * .03)))
        score_size = max(42, min(86, round(height * .096)))
        for index, player in enumerate(self.players):
            color = BLUE if index == 0 else CORAL
            player.avatar.setFixedSize(avatar_size, avatar_size)
            player.name.setStyleSheet(f"font-size: {name_size}px; font-weight: 700;")
            player.score.setStyleSheet(f"color: {color}; font-size: {score_size}px; font-weight: 600;")
            player.score.setFixedWidth(round(score_size * 1.35))
        action_height = max(80, min(128, round(height * .145)))
        self.actions.setFixedHeight(action_height)
        self.turn_banner.setMaximumHeight(max(74, min(120, round(height * .16))))
        for control in (self.actions.hint, self.actions.undo, self.actions.pause):
            control.setStyleSheet(f"QPushButton {{ padding: 0; border-radius: 9px; min-height: {action_height}px; }}")
            control.setFixedHeight(action_height)

    def play_human(self, move):
        if not self.board.animating:
            return self.controller.play_human(move)
        return None

    def _sync_motion_input(self):
        busy = self.board.animating
        explanation = "Finishing this move…" if busy else self._explanation
        self.action_explanation.setText(explanation)
        self.compact_explanation.setText(explanation)
        self.action_explanation.setVisible(bool(self._ai_error) and not self.stage.compact)
        self.compact_explanation.setVisible(bool(self._ai_error) and self.stage.compact)
        for actions in (self.actions, self.compact_actions):
            actions.hint.setEnabled(self.controller.accepts_human_move and not busy)
            actions.undo.setEnabled(self.controller.can_undo and not busy)
            for control in (actions.hint, actions.undo):
                reason = ("Suggest an available edge." if control is actions.hint and control.isEnabled()
                          else explanation)
                control.setToolTip(reason)
                control.setAccessibleDescription(reason)

    def _selection_changed(self, text):
        self.keyboard_help.setText(text + "  ·  Enter: draw · H / V: direction"
                                   if self.board.keyboard_selection else self._keyboard_instructions)
        self.keyboard_help.setVisible(self.board.keyboard_selection and self.board.hasFocus()
                                      and self.height() >= 540 and not self.engine.finished)

    def _schedule(self, delay, callback):
        if self.motion_policy and self.motion_policy.enabled:
            delay = max(AI_MOVE_MS, delay)
        timer = QTimer(self)
        timer.setSingleShot(True)
        self.timers.add(timer)

        def fire():
            self.timers.discard(timer)
            timer.deleteLater()
            try:
                callback()
            except ImportError:
                # Native runtime failures must leave the board safely paused.
                # Do not replace the selected strategy or bypass OS controls.
                self._ai_error = ("Computer play is unavailable. Resume to retry, "
                                  "or choose Home and play with a friend.")
                self.controller.pause()

        timer.timeout.connect(fire)
        timer.start(delay)
        return timer

    def _cancel(self, timer):
        timer.stop()
        self.timers.discard(timer)
        timer.deleteLater()

    def start(self, config):
        self.board.finish_feedback()
        self._ai_error = ""
        self.board.selected = Move("row", (0, 0))
        self.board.keyboard_selection = False
        self.controller.start(config)
        self.board.setFocus()

    def rematch(self):
        """Immediately begin another round with the same opponent and names."""
        self.start(self.controller.config)

    def stop(self):
        self.controller.stop()
        self.board.refresh(False, False, self.controller.config.player_names)
        self.board.finish_feedback()

    def _on_move(self, outcome):
        if outcome is not None:
            self.sound_requested.emit("result" if outcome.finished else
                                      "capture" if outcome.captured_boxes else "move")
        if outcome is None:
            self.board.finish_feedback()
        if outcome is not None:
            self._ai_error = ""
        config = self.controller.config
        paused = self.controller.paused
        finished = self.engine.finished
        current = self.engine.current_player
        if finished:
            winner = 0 if self.engine.scores[0] > self.engine.scores[1] else 1
            turn = ("You win!" if config.player_names[winner].lower() == "you"
                    else f"{config.player_names[winner]} wins!")
        elif paused:
            turn = "Match paused"
        elif config.mode == "AI" and current == 2:
            turn = "Computer is thinking…"
        else:
            name = config.player_names[current - 1]
            turn = "Your turn" if name.lower() == "you" else f"{name}’s turn"
        self.turn_banner.setText(turn)
        self.result_banner.setText(turn)
        self.mode_label.setText(f"VS COMPUTER / {config.difficulty.upper()}"
                                if config.mode == "AI" else "TWO PLAYERS")
        self.remaining.setText(f"{25 - sum(self.engine.scores)} boxes left")
        self.remaining.setAccessibleName(f"{25 - sum(self.engine.scores)} boxes remaining")
        for index, player in enumerate(self.players):
            player.refresh(config.player_names[index], self.engine.scores[index],
                           current == index + 1 and not finished and not paused)
        for index, compact_player in enumerate(self.compact_players):
            compact_player.refresh(config.player_names[index], self.engine.scores[index],
                                   current == index + 1 and not finished and not paused)
        self.compact_turn.setText(f"{turn}   ·   {25 - sum(self.engine.scores)} left")
        self.board.refresh(self.controller.accepts_human_move, paused, config.player_names)
        if outcome is not None:
            self.board.animate_move(outcome)
        if finished:
            explanation = "All 25 boxes claimed. Rematch keeps the same players and difficulty."
        elif paused:
            explanation = "Resume to draw lines, ask for a hint, or undo."
        elif config.mode == "AI":
            explanation = ("Hints return on your turn. Undo is for two-player games."
                           if current == 2 else "Undo is available in two-player games.")
        elif not self.engine.history:
            explanation = "Undo becomes available after a non-scoring move."
        elif not self.engine.can_undo:
            explanation = "A move that captures a box cannot be undone."
        else:
            explanation = "Undo removes the last non-scoring move."
        explanation = self._ai_error or explanation
        self._explanation = explanation
        for actions in (self.actions, self.compact_actions):
            actions.pause.setEnabled(self.controller.active)
            actions.pause.setText("Resume" if paused else "Pause")
        self._sync_motion_input()
        self._sync_composition()
        if finished:
            self.result_summary.setText(
                f'<span style="color:{BLUE};font-size:64px">{self.engine.scores[0]}</span>'
                f'<span style="color:#5B6465;font-size:46px"> – </span>'
                f'<span style="color:{CORAL};font-size:64px">{self.engine.scores[1]}</span>')
            self.result_names.setText(f"{config.player_names[0]} {self.engine.scores[0]}  ·  "
                                      f"{config.player_names[1]} {self.engine.scores[1]}")
            self.result_summary.setAccessibleName(
                f"Final score: {config.player_names[0]} {self.engine.scores[0]}, "
                f"{config.player_names[1]} {self.engine.scores[1]}")
        if finished:
            self.caption.setText("Every line made a difference.")
        elif outcome and outcome.captured_boxes:
            self.caption.setText(f"+{len(outcome.captured_boxes)} · Complete a box. Play again.")
        else:
            self.caption.setText("Complete a box. Play again." if not finished else "Every line made a difference.")
        self.stage.arrange()

    def _on_finished(self, outcome):
        (self.compact_rematch if self.stage.compact else self.rematch_button).setFocus()

    def show_hint(self):
        if not self.board.animating:
            self.board.show_hint(self.controller.get_hint())

    def undo(self):
        if not self.board.animating and self.controller.undo_move():
            self.board.setFocus()

    def toggle_pause(self):
        if self.controller.paused:
            self._ai_error = ""
            self.controller.resume()
            self.board.setFocus()
        elif self.controller.pause():
            (self.compact_actions if self.stage.compact else self.actions).pause.setFocus()
            self.pause_requested.emit()

    def _sync_composition(self):
        compact = self.stage.compact
        finished = self.engine.finished
        self.sidebar.setVisible(not compact)
        self.compact_strip.setVisible(compact)
        self.compact_actions.setVisible(compact and not finished)
        self.compact_results.setVisible(compact and finished)
        self.header.setVisible(not compact)
        self.remaining.setVisible(not finished)
        for player in self.players:
            player.setVisible(not finished)
        self.actions.setVisible(not finished)
        self.turn_banner.setVisible(not finished)
        self.result_group.setVisible(finished)
        self.action_explanation.setVisible(bool(self._ai_error) and not compact)
        self.compact_explanation.setVisible(bool(self._ai_error) and compact)

    def resizeEvent(self, event):
        compact = self.width() < 960 or self.height() < 580
        short = self.height() < 500
        self.stage.compact = compact
        self._sync_composition()
        self.caption.setVisible(not short)
        self.keyboard_help.setVisible(not short and self.board.keyboard_selection
                                      and self.board.hasFocus() and not self.engine.finished)
        self.stage.arrange()
        super().resizeEvent(event)
