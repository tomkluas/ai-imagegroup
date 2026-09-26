from __future__ import annotations

import os
from collections import OrderedDict
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QSize, Qt, QThreadPool, Signal, Slot
from PySide6.QtGui import QColor, QImage, QImageReader, QPainter, QPixmap


def placeholder_pixmap(size: QSize, message: str = "图片不可用") -> QPixmap:
    pixmap = QPixmap(size)
    pixmap.fill(QColor("#e5e7eb"))
    painter = QPainter(pixmap)
    painter.setPen(QColor("#6b7280"))
    painter.drawText(pixmap.rect(), Qt.AlignCenter | Qt.TextWordWrap, message)
    painter.end()
    return pixmap


def read_thumbnail_image(path: Path, size: QSize) -> tuple[QImage, bool]:
    path = Path(path)
    if not path.is_file():
        return QImage(), False

    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    original_size = reader.size()
    if original_size.isValid():
        reader.setScaledSize(original_size.scaled(size, Qt.KeepAspectRatio))
    image = reader.read()
    if image.isNull():
        return QImage(), False
    return image, True


def load_thumbnail(path: Path, size: QSize) -> tuple[QPixmap, bool]:
    image, available = read_thumbnail_image(path, size)
    if not available:
        return placeholder_pixmap(size), False
    return QPixmap.fromImage(image), True


class _ThumbnailSignals(QObject):
    finished = Signal(int, object, object, object, bool)


class _ThumbnailTask(QRunnable):
    def __init__(self, batch, request_key, cache_key, path, size):
        super().__init__()
        self.batch = batch
        self.request_key = request_key
        self.cache_key = cache_key
        self.path = path
        self.size = size
        self.signals = _ThumbnailSignals()

    @Slot()
    def run(self):
        image, available = read_thumbnail_image(self.path, self.size)
        self.signals.finished.emit(
            self.batch, self.request_key, self.cache_key, image, available
        )


class AsyncThumbnailLoader(QObject):
    loaded = Signal(object, object, bool)

    def __init__(self, parent=None, max_workers=None, cache_limit=256):
        super().__init__(parent)
        detected_cpus = os.cpu_count() or 2
        workers = max_workers or max(1, min(2, detected_cpus - 1))
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(workers)
        self.cache_limit = cache_limit
        self.cache = OrderedDict()
        self.batch = 0

    def begin_batch(self):
        self.batch += 1
        self.pool.clear()
        return self.batch

    def request(self, path: Path, size: QSize, request_key):
        path = Path(path)
        cache_key = (str(path), size.width(), size.height())
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.cache.move_to_end(cache_key)
            image, available = cached
            self.loaded.emit(request_key, image, available)
            return

        task = _ThumbnailTask(self.batch, request_key, cache_key, path, size)
        task.signals.finished.connect(self._task_finished)
        self.pool.start(task)

    @Slot(int, object, object, object, bool)
    def _task_finished(self, batch, request_key, cache_key, image, available):
        if batch != self.batch:
            return
        self.cache[cache_key] = (image, available)
        self.cache.move_to_end(cache_key)
        while len(self.cache) > self.cache_limit:
            self.cache.popitem(last=False)
        self.loaded.emit(request_key, image, available)
