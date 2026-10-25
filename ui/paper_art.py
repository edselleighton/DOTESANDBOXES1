"""Resolution-independent Paper Club lettering and stationery icons."""

import math

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class PaperLogo(QWidget):
    """The multicolour wordmark, rendered with the bundled bold Fredoka font."""

    def __init__(self, stacked=False, parent=None):
        super().__init__(parent)
        self.stacked = stacked
        self.setAccessibleName("Dots and Boxes")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def sizeHint(self):
        return QSize(350, 230 if self.stacked else 52)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("Fredoka")
        font.setStyleName("Bold")
        font.setWeight(QFont.Weight.Bold)
        font.setPixelSize(100)
        parts = []
        cursor = 0.0
        for text, color in (("DOTS", "#173D60"), ("&", "#7D916D"), ("BOXES", "#CB513C")):
            path = QPainterPath()
            path.addText(0, 0, font, text)
            path.setFillRule(Qt.FillRule.WindingFill)
            bounds = path.boundingRect()
            if self.stacked and text == "BOXES":
                cursor = 0
            path.translate(cursor - bounds.left(), -bounds.top() + (90 if self.stacked and text == "BOXES" else 0))
            parts.append((path, color))
            cursor += bounds.width() + (12 if self.stacked else 18)
        bounds = parts[0][0].boundingRect()
        for path, _ in parts[1:]:
            bounds = bounds.united(path.boundingRect())
        available = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        scale = min(available.width() / bounds.width(), available.height() / (bounds.height() + (21 if self.stacked else 0)))
        painter.translate(available.center().x() - bounds.width() * scale / 2,
                          available.center().y() - (bounds.height() + (21 if self.stacked else 0)) * scale / 2)
        painter.scale(scale, scale)
        painter.setPen(Qt.PenStyle.NoPen)
        for path, color in parts:
            painter.fillPath(path, QColor(color))
        if self.stacked:
            underline = QPainterPath(QPointF(5, bounds.bottom() + 15))
            underline.cubicTo(bounds.width() * .3, bounds.bottom() + 5,
                              bounds.width() * .7, bounds.bottom() + 8,
                              bounds.width() - 5, bounds.bottom() + 16)
            painter.setPen(QPen(QColor("#8C9D7A"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawPath(underline)


def paper_icon(name, color="#20394A", size=24):
    """Paint a consistent icon without platform-dependent emoji or symbol fonts."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size / 24, size / 24)
    ink = QColor(color)
    painter.setPen(QPen(ink, 1.9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    if name == "play":
        path.moveTo(7, 3); path.lineTo(20, 12); path.lineTo(7, 21); path.closeSubpath()
        painter.fillPath(path, ink)
    elif name == "book":
        path.moveTo(12, 5); path.cubicTo(9, 3, 5, 3, 2, 4); path.lineTo(2, 20)
        path.cubicTo(6, 18, 9, 19, 12, 21); path.cubicTo(15, 19, 18, 18, 22, 20)
        path.lineTo(22, 4); path.cubicTo(18, 3, 15, 3, 12, 5); path.lineTo(12, 21)
        painter.drawPath(path)
    elif name == "trophy":
        path.moveTo(7, 3); path.lineTo(17, 3); path.lineTo(17, 9)
        path.cubicTo(17, 17, 7, 17, 7, 9); path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(12, 15, 12, 21); painter.drawLine(7, 22, 17, 22)
        path = QPainterPath(QPointF(7, 5)); path.lineTo(3, 5); path.cubicTo(2, 11, 5, 12, 8, 12)
        path.moveTo(17, 5); path.lineTo(21, 5); path.cubicTo(22, 11, 19, 12, 16, 12)
        painter.drawPath(path)
    elif name == "settings":
        for index in range(32):
            angle = math.pi * 2 * index / 32
            radius = 10 if index % 4 in (1, 2) else 7.8
            point = QPointF(12 + math.cos(angle) * radius, 12 + math.sin(angle) * radius)
            path.moveTo(point) if index == 0 else path.lineTo(point)
        path.closeSubpath(); path.addEllipse(QRectF(8.5, 8.5, 7, 7))
        painter.fillPath(path, ink)
    elif name == "home":
        path.moveTo(2, 11); path.lineTo(12, 2); path.lineTo(22, 11)
        path.lineTo(19, 11); path.lineTo(19, 22); path.lineTo(14, 22)
        path.lineTo(14, 15); path.lineTo(10, 15); path.lineTo(10, 22)
        path.lineTo(5, 22); path.lineTo(5, 11); path.closeSubpath()
        painter.fillPath(path, ink)
    elif name == "pause":
        painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(ink)
        painter.drawRoundedRect(QRectF(6, 3, 4, 18), 1, 1)
        painter.drawRoundedRect(QRectF(14, 3, 4, 18), 1, 1)
    elif name == "hint":
        path.moveTo(9, 17); path.cubicTo(9, 13, 5, 12, 5, 8)
        path.cubicTo(5, -1, 19, -1, 19, 8); path.cubicTo(19, 12, 15, 13, 15, 17)
        path.closeSubpath(); painter.drawPath(path)
        painter.drawLine(9, 20, 15, 20); painter.drawLine(11, 23, 13, 23)
    elif name == "undo":
        path.moveTo(9, 3); path.lineTo(3, 9); path.lineTo(9, 15)
        path.moveTo(3, 9); path.lineTo(13, 9); path.cubicTo(22, 9, 22, 21, 15, 21)
        painter.drawPath(path)
    painter.end()
    return QIcon(pixmap)
