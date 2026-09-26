from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QImageReader, QPainter, QPixmap


def placeholder_pixmap(size: QSize, message: str = "图片不可用") -> QPixmap:
    pixmap = QPixmap(size)
    pixmap.fill(QColor("#e5e7eb"))
    painter = QPainter(pixmap)
    painter.setPen(QColor("#6b7280"))
    painter.drawText(pixmap.rect(), Qt.AlignCenter | Qt.TextWordWrap, message)
    painter.end()
    return pixmap


def load_thumbnail(path: Path, size: QSize) -> tuple[QPixmap, bool]:
    path = Path(path)
    if not path.is_file():
        return placeholder_pixmap(size), False

    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    original_size = reader.size()
    if original_size.isValid():
        reader.setScaledSize(original_size.scaled(size, Qt.KeepAspectRatio))
    image = reader.read()
    if image.isNull():
        return placeholder_pixmap(size, "图片损坏"), False
    return QPixmap.fromImage(image), True
