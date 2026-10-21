"""Paper Club match composition, native controls and Qt timer ownership."""

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from core.game_engine import GameEngine, Move
from core.match_controller import MatchController
from ui.paper_style import BLUE, CORAL, INK, PaperSurface, button, label
from ui.qt_board import GameBoard


class Avatar(QWidget):
    def __init__(self, color):
        super().__init__()
        self.color = color
        self.setFixedSize(56, 56)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
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
        self.setMinimumHeight(72)
        self.setObjectName("turnBanner")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(12, 8, -12, -8)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#D6DEC8"))
        painter.drawRoundedRect(rect, 5, 5)
        painter.setPen(QPen(QColor("#D6DEC8"), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(rect.topLeft(), rect.topRight())
        painter.end()
        super().paintEvent(event)


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
        self.layout.setContentsMargins(0, 4, 0, 4)
        self.layout.setSpacing(12)
        self.avatar = Avatar(color)
        self.name = PlayerName(role)
        self.name.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.score = label("0", "matchScore")
        self.score.setStyleSheet(f"color: {color};")
        self.score.setFixedWidth(52)
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


def action_icon(kind, color):
    pixmap = QPixmap(44, 44)
    pixmap.setDevicePixelRatio(2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(color), 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                        Qt.PenJoinStyle.RoundJoin))
    if kind == "hint":
        painter.drawEllipse(QRectF(5, 2, 12, 12))
        painter.drawLine(QPointF(8, 13), QPointF(8, 18))
        painter.drawLine(QPointF(14, 13), QPointF(14, 18))
        painter.drawLine(QPointF(8, 18), QPointF(14, 18))
        painter.drawLine(QPointF(9, 21), QPointF(13, 21))
    elif kind == "undo":
        path = QPainterPath(QPointF(5, 8))
        path.cubicTo(19, 4, 22, 19, 11, 19)
        painter.drawPath(path)
        painter.drawLine(QPointF(5, 8), QPointF(5, 3))
        painter.drawLine(QPointF(5, 8), QPointF(10, 10))
    elif kind == "pause":
        painter.drawLine(QPointF(8, 4), QPointF(8, 19))
        painter.drawLine(QPointF(14, 4), QPointF(14, 19))
    else:
        path = QPainterPath(QPointF(7, 3))
        path.lineTo(18, 11)
        path.lineTo(7, 19)
        path.closeSubpath()
        painter.drawPath(path)
    painter.end()
    return QIcon(pixmap)


class MatchActions(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.hint = button("Hint", "primary")
        self.undo = button("Undo")
        self.pause = button("Pause")
        for control, kind in ((self.hint, "hint"), (self.undo, "undo"), (self.pause, "pause")):
            control.setStyleSheet("QPushButton { padding-left: 8px; padding-right: 8px; }")
            control.setIcon(action_icon(kind, "#FFFFFF" if kind == "hint" else INK))
            control.setIconSize(QSize(18, 18))
            layout.addWidget(control, 1)


class MatchStage(QWidget):
    """Keep paper sheets aligned and bound board size by both available axes."""
    def __init__(self, board_sheet, sidebar, header):
        super().__init__()
        self.board_sheet = board_sheet
        self.sidebar = sidebar
        self.header = header
        board_sheet.setParent(self)
        sidebar.setParent(self)
        header.setParent(self)
        self.compact = False
        self.setMinimumSize(200, 200)

    def arrange(self):
        height = max(1, self.height())
        if self.compact:
            side = min(self.width(), height)
            self.board_sheet.setGeometry((self.width() - side) // 2, 0, side, side)
        else:
            sidebar_width = 320
            board_side = min(700, height - 56, self.width() - sidebar_width - 16)
            left = (self.width() - board_side - sidebar_width - 16) // 2
            top = (height - board_side - 56) // 2
            self.header.setGeometry(left, top, board_side + sidebar_width + 16, 48)
            self.board_sheet.setGeometry(left, top + 56, board_side, board_side)
            self.sidebar.setGeometry(left + board_side + 16, top + 56, sidebar_width, board_side)

    def resizeEvent(self, event):
        self.arrange()
        super().resizeEvent(event)


class MatchPage(QWidget):
    home_requested = Signal()
    new_match_requested = Signal()

    def __init__(self):
        super().__init__()
        self.engine = GameEngine()
        self._ai_error = ""
        self.timers = set()
        self.controller = MatchController(self.engine, self._schedule, self._cancel,
                                          self._on_move, self._on_finished)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(8)
        self.header = QWidget()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(8, 0, 8, 0)
        self.title = label('<span style="color:#265A80">DOTS</span> &amp; '
                           '<span style="color:#CB513C">BOXES</span>', "heading")
        self.mode_label = label("", "fieldLabel")
        self.home_button = button("Home", "quiet")
        self.home_button.clicked.connect(self.home_requested)
        header_layout.addWidget(self.title)
        header_layout.addSpacing(16)
        header_layout.addWidget(self.mode_label, 1)
        header_layout.addWidget(self.home_button)

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
        board_layout.setContentsMargins(12, 12, 12, 24)
        board_layout.setSpacing(0)
        self.board = GameBoard(self.engine)
        self.board.move_requested.connect(self.controller.play_human)
        board_layout.addWidget(self.board, 1)
        self.caption = label("Complete a box. Play again.", "boardCaption")
        self.caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        board_layout.addWidget(self.caption)
        self.sidebar = PaperSurface()
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(24, 20, 24, 32)
        side_layout.setSpacing(12)
        self.turn_banner = TurnBanner()
        self.turn_banner.setTextFormat(Qt.TextFormat.PlainText)
        self.turn_banner.setMaximumHeight(104)
        side_layout.addWidget(self.turn_banner, 1)
        self.players = (PlayerRow(BLUE, "blueLabel"), PlayerRow(CORAL, "coralLabel"))
        for player in self.players:
            player.setMaximumHeight(120)
            side_layout.addWidget(player, 2)
        self.remaining = label("", "remainingBoxes")
        self.remaining.setMaximumHeight(80)
        side_layout.addWidget(self.remaining, 1)
        self.action_explanation = label("", "secondary")
        self.action_explanation.setMinimumHeight(56)
        self.action_explanation.setMaximumHeight(80)
        side_layout.addWidget(self.action_explanation, 1)
        self.actions = MatchActions()
        self.actions.setMaximumHeight(72)
        side_layout.addWidget(self.actions)
        self.new_button = button("New game", "quiet")
        self.new_button.clicked.connect(self.new_match_requested)
        side_layout.addWidget(self.new_button)
        self.stage = MatchStage(self.board_sheet, self.sidebar, self.header)
        self.root_layout.addWidget(self.stage, 1)

        self.compact_actions = MatchActions()
        self.compact_home = button("Home", "quiet")
        self.compact_home.clicked.connect(self.home_requested)
        self.compact_actions.layout().addWidget(self.compact_home, 1)
        self.root_layout.addWidget(self.compact_actions)
        self.compact_explanation = label("", "secondary")
        self.compact_explanation.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.root_layout.addWidget(self.compact_explanation)
        self._keyboard_instructions = "Arrows: select · H / V: direction · Enter: draw · Tab: controls"
        self.keyboard_help = label(self._keyboard_instructions, "secondary")
        self.keyboard_help.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.root_layout.addWidget(self.keyboard_help)
        self.board.selection_changed.connect(self._selection_changed)
        self.board.setToolTip(self.board.accessibleDescription())
        for actions in (self.actions, self.compact_actions):
            actions.hint.clicked.connect(self.show_hint)
            actions.undo.clicked.connect(self.undo)
            actions.pause.clicked.connect(self.toggle_pause)
        QWidget.setTabOrder(self.home_button, self.board)
        QWidget.setTabOrder(self.board, self.actions.hint)
        QWidget.setTabOrder(self.actions.hint, self.actions.undo)
        QWidget.setTabOrder(self.actions.undo, self.actions.pause)
        QWidget.setTabOrder(self.actions.pause, self.new_button)
        QWidget.setTabOrder(self.new_button, self.compact_actions.hint)
        QWidget.setTabOrder(self.compact_actions.hint, self.compact_actions.undo)
        QWidget.setTabOrder(self.compact_actions.undo, self.compact_actions.pause)
        QWidget.setTabOrder(self.compact_actions.pause, self.compact_home)

    def _selection_changed(self, text):
        self.keyboard_help.setText(text + "  ·  Enter: draw · H / V: direction"
                                   if self.board.keyboard_selection else self._keyboard_instructions)

    def _schedule(self, delay, callback):
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
        self._ai_error = ""
        self.board.selected = Move("row", (0, 0))
        self.board.keyboard_selection = False
        self.controller.start(config)
        self.board.setFocus()

    def stop(self):
        self.controller.stop()

    def _on_move(self, outcome):
        if outcome is not None:
            self._ai_error = ""
        config = self.controller.config
        paused = self.controller.paused
        finished = self.engine.finished
        current = self.engine.current_player
        if finished:
            winner = 0 if self.engine.scores[0] > self.engine.scores[1] else 1
            turn = f"{config.player_names[winner]} wins!"
        elif paused:
            turn = "Match paused"
        elif config.mode == "AI" and current == 2:
            turn = "Computer is thinking…"
        else:
            turn = f"{config.player_names[current - 1]}’s turn"
        self.turn_banner.setText(turn)
        self.mode_label.setText(f"VS COMPUTER / {config.difficulty.upper()}"
                                if config.mode == "AI" else "TWO PLAYERS")
        self.remaining.setText(f"{25 - sum(self.engine.scores)} boxes left")
        for index, player in enumerate(self.players):
            player.refresh(config.player_names[index], self.engine.scores[index],
                           current == index + 1 and not finished and not paused)
        for index, compact_player in enumerate(self.compact_players):
            compact_player.refresh(config.player_names[index], self.engine.scores[index],
                                   current == index + 1 and not finished and not paused)
        self.compact_turn.setText(f"{turn}   ·   {25 - sum(self.engine.scores)} left")
        self.board.refresh(self.controller.accepts_human_move, paused, config.player_names)
        if finished:
            explanation = "All 25 boxes claimed. Start a new game from Home."
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
        self.action_explanation.setText(explanation)
        self.compact_explanation.setText(explanation)
        for actions in (self.actions, self.compact_actions):
            actions.hint.setEnabled(self.controller.accepts_human_move)
            actions.undo.setEnabled(self.controller.can_undo)
            actions.pause.setEnabled(self.controller.active)
            actions.pause.setText("Resume" if paused else "Pause")
            actions.pause.setIcon(action_icon("resume" if paused else "pause", INK))
            for control in (actions.hint, actions.undo):
                reason = ("Suggest an available edge." if control is actions.hint and control.isEnabled()
                          else explanation)
                control.setToolTip(reason)
                control.setAccessibleDescription(reason)
        self.new_button.setVisible(finished)
        if outcome and outcome.captured_boxes:
            self.caption.setText(f"+{len(outcome.captured_boxes)} · Complete a box. Play again.")
        else:
            self.caption.setText("Complete a box. Play again." if not finished else "Every line made a difference.")
        self.stage.arrange()

    def _on_finished(self, outcome):
        # Keep the completed board and final scores visible; the full results
        # experience and rematch controls belong to the results milestone.
        self.new_button.setFocus() if not self.stage.compact else self.compact_home.setFocus()

    def show_hint(self):
        self.board.show_hint(self.controller.get_hint())

    def undo(self):
        if self.controller.undo_move():
            self.board.setFocus()

    def toggle_pause(self):
        if self.controller.paused:
            self._ai_error = ""
            self.controller.resume()
            self.board.setFocus()
        elif self.controller.pause():
            (self.compact_actions if self.stage.compact else self.actions).pause.setFocus()

    def resizeEvent(self, event):
        compact = self.width() < 1000 or self.height() < 620
        short = self.height() < 500
        self.stage.compact = compact
        self.sidebar.setVisible(not compact)
        self.compact_strip.setVisible(compact)
        self.compact_actions.setVisible(compact)
        self.compact_explanation.setVisible(compact)
        self.caption.setVisible(not short)
        self.keyboard_help.setVisible(not short)
        self.title.setVisible(not short)
        self.header.setVisible(not compact)
        self.stage.arrange()
        super().resizeEvent(event)
