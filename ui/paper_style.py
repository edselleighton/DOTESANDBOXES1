"""Shared Paper Club surfaces and native-control styling."""

import random

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QWidget
from ui.motion_controls import MotionButton

from utils.assets import asset_path

INK = "#233D3A"
BLUE = "#265A80"
CORAL = "#CB513C"
SAGE = "#57704F"
PAPER = "#FFF9EC"


def load_heading_font():
    font_id = QFontDatabase.addApplicationFont(asset_path("fonts/Fredoka.ttf"))
    families = QFontDatabase.applicationFontFamilies(font_id)
    return families[0] if families else "Segoe UI"


def stylesheet(heading_font):
    return """
        QWidget { color: #233D3A; font-family: 'Segoe UI'; font-size: 15px; }
        QMainWindow { background: #F1E7D1; }
        QStackedWidget { background: transparent; }
        QStackedWidget > QWidget, QLabel { background: transparent; }
        QLabel#brand { font-family: '%s'; font-size: 21px; font-weight: 600;
                       background: #FFF9EC; border-radius: 8px; padding: 6px 12px; }
        QLabel#homeTitle { font-family: '%s'; font-size: 72px; font-weight: 600; }
        QLabel#heading { font-family: '%s'; font-size: 32px; font-weight: 500; }
        QLabel#eyebrow { font-size: 12px; font-weight: 600; color: #52684C; letter-spacing: 2px; }
        QLabel#lead { font-size: 19px; }
        QLabel#secondary { font-size: 14px; color: #56635C; }
        QLabel#fieldLabel { font-size: 14px; font-weight: 600; }
        QLabel#matchScore { font-family: '%s'; font-size: 42px; font-weight: 600; }
        QLabel#turnBanner { font-family: '%s'; font-size: 25px; font-weight: 500; padding: 12px 20px; }
        QLabel#remainingBoxes { font-size: 18px; padding: 16px 0;
                                border-top: 1px solid #D7CCB7; border-bottom: 1px solid #D7CCB7; }
        QLabel#boardCaption { font-size: 14px; color: #233D3A; padding-bottom: 4px; }
        QLabel#blueLabel { font-size: 14px; font-weight: 600; color: #265A80; }
        QLabel#coralLabel { font-size: 14px; font-weight: 600; color: #B44332; }
        QLabel#error { color: #A52D23; font-size: 14px; }
        QPushButton { background: #FFF9EC; border: 1px solid #B8AD95;
                      border-radius: 9px; padding: 10px 18px; min-height: 22px; }
        QPushButton:hover { background: #EAE7D4; border-color: #6B7C60; }
        QPushButton:pressed { background: #DBDFC9; }
        QPushButton:focus { border: 2px solid #265A80; padding: 9px 17px; }
        QPushButton#primary { background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                              stop:0 #607951, stop:1 #506D4D); color: #FFFFFF; border-color: #526949;
                              font-size: 17px; font-weight: 600; padding: 12px 24px; }
        QPushButton#primary:hover { background: #465E3F; }
        QPushButton#primary:pressed { background: #374C32; }
        QPushButton#primary:focus { border: 2px solid #233D3A; padding: 11px 23px; }
        QPushButton#quiet { background: #FFF9EC; border-color: transparent; }
        QPushButton#quiet:hover { background: #E4E7D6; }
        QPushButton#quiet:focus { border-color: #265A80; }
        QPushButton#homeLink { background: transparent; border: 0;
                              border-bottom: 1px solid #D7CCB7; border-radius: 0;
                              text-align: left; padding: 7px 9px; color: #20394A; font-size: 18px; }
        QPushButton#homeLink:hover { background: #E9E7D4; }
        QPushButton#homeLink:focus { border: 2px solid #265A80; padding: 5px 7px; }
        QPushButton#homeLink:disabled { background: transparent; color: #71766B;
                                       border-bottom: 1px solid #D7CCB7; }
        QLabel#homeTagline { color: #20394A; font-weight: 500; }
        QPushButton:checked { background: #DCE6D4; border: 2px solid #57704F; padding: 9px 17px; }
        QPushButton:disabled { color: #7B7B70; background: #EAE6DC; border-color: #D0C9B9; }
        QPushButton#primary:disabled { color: #7B7B70; background: #EAE6DC; border-color: #D0C9B9; }
        QLineEdit { background: #FFFCF5; border: 1px solid #B8AD95; border-radius: 7px;
                    padding: 10px 12px; min-height: 22px; selection-background-color: #DCE6D4;
                    selection-color: #233D3A; }
        QLineEdit:focus { border: 2px solid #265A80; padding: 9px 11px; }
        QLineEdit:disabled { color: #666C64; background: #EDE9DE; }
        QMenuBar, QMenu { background: #FFF9EC; }
        QMenuBar::item:selected, QMenu::item:selected { background: #DCE6D4; }
        QToolTip { color: #233D3A; background: #FFF9EC; border: 1px solid #B8AD95; }
    """ % (heading_font, heading_font, heading_font, heading_font, heading_font)


def label(text, role="secondary"):
    widget = QLabel(text)
    widget.setObjectName(role)
    widget.setWordWrap(True)
    return widget


def button(text, role="", checkable=False):
    widget = MotionButton(text)
    widget.setObjectName(role)
    widget.setCheckable(checkable)
    widget.setMinimumHeight(44)
    return widget


class Tabletop(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._background = QPixmap(asset_path("paper-tabletop.png"))
        self._scaled = QPixmap()

    def resizeEvent(self, event):
        if not self._background.isNull():
            self._scaled = self._background.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#F1E7D1"))
        if not self._scaled.isNull():
            painter.drawPixmap((self.width() - self._scaled.width()) // 2,
                               (self.height() - self._scaled.height()) // 2, self._scaled)


class PaperSurface(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._grain = QPixmap(96, 96)
        self._grain.fill(Qt.GlobalColor.transparent)
        painter = QPainter(self._grain)
        rng = random.Random(17)
        painter.setPen(QColor(110, 90, 58, 20))
        for _ in range(700):
            painter.drawPoint(rng.randrange(96), rng.randrange(96))
        painter.end()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(5, 4, -7, -12)
        painter.setPen(Qt.PenStyle.NoPen)
        for offset, alpha in ((8, 8), (5, 12), (3, 16)):
            painter.setBrush(QColor(70, 51, 25, alpha))
            painter.drawRoundedRect(rect.translated(2, offset), 12, 12)
        painter.setBrush(QColor("#E5DEC8"))
        painter.drawRoundedRect(rect.translated(2, 3), 10, 10)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor("#FFFCF3"))
        gradient.setColorAt(1, QColor("#F4E8D3"))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor("#DFD1B9"), 1))
        painter.drawRoundedRect(rect, 10, 10)
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)
        painter.setClipPath(path)
        painter.drawTiledPixmap(rect, self._grain)


class BoardIllustration(QWidget):
    """Decorative welcome illustration, deliberately separate from the game board."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(0, 0)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAccessibleName("Dots and Boxes tabletop illustration")
        self.setAccessibleDescription("Blue and coral lines complete boxes on a paper board")

    def sizeHint(self):
        return QSize(400, 400)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(6)
        side = min(self.width(), self.height()) * 0.85
        paper = QRectF(-side / 2, -side / 2, side, side)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.save()
        painter.rotate(-17)
        painter.setBrush(QColor("#9BA986"))
        painter.drawRoundedRect(paper.adjusted(-8, -4, 6, 12).translated(0, 11), 5, 5)
        painter.restore()
        painter.setBrush(QColor(74, 56, 31, 20))
        painter.drawRoundedRect(paper.translated(5, 9), 12, 12)
        gradient = QLinearGradient(paper.topLeft(), paper.bottomRight())
        gradient.setColorAt(0, QColor("#FFFBEE"))
        gradient.setColorAt(1, QColor("#F1E1C5"))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor("#D9C5A1"), 1))
        painter.drawRoundedRect(paper, 12, 12)
        rng = random.Random(5)
        painter.setPen(QColor(126, 99, 58, 24))
        for _ in range(1400):
            painter.drawPoint(QRectF(paper.left() + rng.random() * side,
                                    paper.top() + rng.random() * side, 0, 0).topLeft())
        gap = side * 0.148
        start = -gap * 2.5

        def point(x, y):
            return start + x * gap, start + y * gap

        boxes = ((1, 1, 1), (3, 3, 2))
        for x, y, owner in boxes:
            px, py = point(x, y)
            painter.fillRect(QRectF(px, py, gap, gap),
                             QColor("#CFE2EC" if owner == 1 else "#F6D4C4"))
            painter.setPen(QColor(BLUE if owner == 1 else CORAL))
            font = QFont("Segoe UI")
            font.setPixelSize(max(12, round(side / 24)))
            font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(font)
            painter.drawText(QRectF(px, py, gap, gap), Qt.AlignmentFlag.AlignCenter,
                             "A" if owner == 1 else "C")
        painter.setPen(QPen(QColor("#D5C9B1"), 1))
        for index in range(6):
            x, y = point(index, index)
            painter.drawLine(QRectF(x, start, 0, gap * 5).topLeft(),
                             QRectF(x, start, 0, gap * 5).bottomLeft())
            painter.drawLine(QRectF(start, y, gap * 5, 0).topLeft(),
                             QRectF(start, y, gap * 5, 0).topRight())
        edges = {}
        for x, y, owner in boxes:
            for edge in (("h", x, y), ("h", x, y + 1), ("v", x, y), ("v", x + 1, y)):
                edges[edge] = owner
        edges.update({("h", 2, 0): 1, ("v", 0, 1): 2, ("v", 0, 2): 1,
                      ("v", 0, 3): 1, ("h", 0, 4): 2, ("h", 1, 5): 1,
                      ("v", 2, 4): 1, ("v", 4, 0): 2, ("h", 4, 1): 1,
                      ("v", 5, 2): 1, ("v", 5, 3): 2, ("h", 4, 4): 1,
                      ("h", 1, 3): 2, ("v", 4, 4): 1})
        for (kind, x, y), owner in edges.items():
            painter.setPen(QPen(QColor(BLUE if owner == 1 else CORAL),
                                max(3, side / 85), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            px, py = point(x, y)
            painter.drawLine(QRectF(px, py, gap if kind == "h" else 0,
                                    gap if kind == "v" else 0).topLeft(),
                             QRectF(px, py, gap if kind == "h" else 0,
                                    gap if kind == "v" else 0).bottomRight())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(INK))
        radius = max(3.5, side / 85)
        for x in range(6):
            for y in range(6):
                px, py = point(x, y)
                painter.drawEllipse(QRectF(px - radius, py - radius, radius * 2, radius * 2))
