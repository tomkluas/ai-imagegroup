import threading
import time
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QImage

from image_group.ui import thumbnails


def test_thumbnail_loader_decodes_off_the_ui_thread(qtbot, monkeypatch):
    started = threading.Event()
    release = threading.Event()

    def slow_read(_path: Path, size: QSize):
        started.set()
        release.wait(timeout=2)
        return QImage(size, QImage.Format_RGB32), True

    monkeypatch.setattr(thumbnails, "read_thumbnail_image", slow_read)
    loader = thumbnails.AsyncThumbnailLoader(max_workers=1)
    results = []
    loader.loaded.connect(lambda key, image, available: results.append((key, image, available)))

    loader.begin_batch()
    loader.request(Path("large.jpg"), QSize(160, 120), "large")
    assert started.wait(timeout=1)
    assert results == []

    release.set()
    qtbot.waitUntil(lambda: len(results) == 1, timeout=2000)
    assert results[0][0] == "large" and results[0][2] is True


def test_thumbnail_loader_discards_results_from_previous_batch(qtbot, monkeypatch):
    old_started = threading.Event()
    release_old = threading.Event()

    def controlled_read(path: Path, size: QSize):
        if path.name == "old.jpg":
            old_started.set()
            release_old.wait(timeout=2)
        return QImage(size, QImage.Format_RGB32), True

    monkeypatch.setattr(thumbnails, "read_thumbnail_image", controlled_read)
    loader = thumbnails.AsyncThumbnailLoader(max_workers=1)
    delivered = []
    loader.loaded.connect(lambda key, _image, _available: delivered.append(key))

    loader.begin_batch()
    loader.request(Path("old.jpg"), QSize(160, 120), "old")
    assert old_started.wait(timeout=1)
    loader.begin_batch()
    loader.request(Path("new.jpg"), QSize(160, 120), "new")
    release_old.set()

    qtbot.waitUntil(lambda: delivered == ["new"], timeout=2000)
    assert "old" not in delivered


def test_thumbnail_request_does_not_stat_on_ui_thread(monkeypatch):
    release = threading.Event()
    original_stat = Path.stat

    def slow_stat(path, *args, **kwargs):
        if path.name == "slow.jpg":
            release.wait(timeout=1)
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", slow_stat)
    timer = threading.Timer(.3, release.set)
    timer.start()
    loader = thumbnails.AsyncThumbnailLoader(max_workers=1)
    loader.begin_batch()
    started = time.monotonic()
    loader.request(Path("slow.jpg"), QSize(160, 120), "slow")
    elapsed = time.monotonic() - started
    release.set(); timer.join()
    assert elapsed < .15
