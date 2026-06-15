"""Painted icon buttons for consistent media controls."""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QPushButton, QWidget


class IconButton(QPushButton):
    def __init__(
        self,
        icon_name: str,
        parent=None,
        *,
        icon_color: str = "#FFFFFF",
    ) -> None:
        super().__init__(parent)
        self.icon_name = icon_name
        self.icon_color = QColor(icon_color)
        self.setText("")
        self.setCursor(Qt.PointingHandCursor)

    def set_icon(self, icon_name: str) -> None:
        self.icon_name = icon_name
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.icon_color)

        rect = self.rect()
        cx = rect.center().x()
        cy = rect.center().y()
        scale = min(rect.width(), rect.height()) / 44

        if self.icon_name == "play":
            self._draw_triangle(painter, cx, cy, scale)
        elif self.icon_name == "pause":
            self._draw_pause(painter, cx, cy, scale)
        elif self.icon_name == "previous":
            self._draw_skip(painter, cx, cy, scale, reverse=True)
        elif self.icon_name == "next":
            self._draw_skip(painter, cx, cy, scale, reverse=False)

    def _draw_triangle(self, painter: QPainter, cx: float, cy: float, scale: float) -> None:
        path = QPainterPath()
        path.moveTo(QPointF(cx - 4 * scale, cy - 8 * scale))
        path.lineTo(QPointF(cx - 4 * scale, cy + 8 * scale))
        path.lineTo(QPointF(cx + 9 * scale, cy))
        path.closeSubpath()
        painter.drawPath(path)

    def _draw_pause(self, painter: QPainter, cx: float, cy: float, scale: float) -> None:
        width = 4.2 * scale
        height = 16 * scale
        gap = 4 * scale
        painter.drawRoundedRect(
            int(cx - gap - width),
            int(cy - height / 2),
            int(width),
            int(height),
            int(2 * scale),
            int(2 * scale),
        )
        painter.drawRoundedRect(
            int(cx + gap),
            int(cy - height / 2),
            int(width),
            int(height),
            int(2 * scale),
            int(2 * scale),
        )

    def _draw_skip(
        self,
        painter: QPainter,
        cx: float,
        cy: float,
        scale: float,
        *,
        reverse: bool,
    ) -> None:
        direction = -1 if reverse else 1
        pen = QPen(self.icon_color)
        pen.setWidthF(2.8 * scale)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        x_bar = cx + direction * 8.5 * scale
        painter.drawLine(
            QPointF(x_bar, cy - 8.5 * scale),
            QPointF(x_bar, cy + 8.5 * scale),
        )

        path = QPainterPath()
        tip = QPointF(cx + direction * 4.5 * scale, cy)
        upper = QPointF(cx - direction * 7.5 * scale, cy - 8.5 * scale)
        lower = QPointF(cx - direction * 7.5 * scale, cy + 8.5 * scale)
        path.moveTo(upper)
        path.lineTo(tip)
        path.lineTo(lower)
        painter.drawPath(path)


class VolumeIcon(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(26, 26)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor("#D8D8D8")
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)

        path = QPainterPath()
        path.moveTo(4, 10)
        path.lineTo(9, 10)
        path.lineTo(15, 5)
        path.lineTo(15, 21)
        path.lineTo(9, 16)
        path.lineTo(4, 16)
        path.closeSubpath()
        painter.drawPath(path)

        painter.setBrush(Qt.NoBrush)
        pen = QPen(color)
        pen.setWidthF(2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(15, 8, 7, 10, -45 * 16, 90 * 16)
