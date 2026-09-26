import threading
import time
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QListView

from image_group.ui import results_page as results_page_module
from image_group.ui import review_page as review_page_module
from image_group.ui import thumbnails
from image_group.ui.new_task_page import NewTaskPage
from image_group.ui.results_page import ResultsPage
from image_group.ui.review_page import ReviewPage


class Scanner:
    def scan(self, paths): return type("Result", (), {"photos":[type("P", (), {"path": Path("a.jpg"), "size":12})()], "duplicates":[], "errors":[]})()
class Controller:
    def __init__(self): self.started = None; self.confirmed = None
    def start(self, name, paths, output, people): self.started = (name, paths, output, people)
    def confirm(self, face_id, person_id): self.confirmed = (face_id, person_id)
class Results:
    def __init__(self, photos=None): self.photos = photos or [Path("1.jpg"), Path("2.jpg")]
    def list_tasks(self): return [{"id":"t1", "name":"今天", "count":2}]
    def list_people(self, task_id): return [{"id":"p1", "name":"张小明", "count":2}]
    def list_photos(self, task_id, person_id): return self.photos

class ReviewController(Controller):
    def __init__(self, cases):
        super().__init__(); self.cases = list(cases)
    def pending_reviews(self): return list(self.cases)
    def confirm(self, face_id, person_id):
        super().confirm(face_id, person_id)
        self.cases = [case for case in self.cases if case["face_id"] != face_id]

def test_new_task_requires_input_output_and_people(qtbot, tmp_path):
    controller = Controller(); page = NewTaskPage(Scanner(), controller, [("p1", "张小明")]); qtbot.addWidget(page)
    assert not page.start_button.isEnabled()
    page.set_input_paths([tmp_path / "photos"]); page.set_output_directory(tmp_path / "out"); page.people_list.item(0).setCheckState(Qt.Checked)
    page.refresh_validity(); assert page.start_button.isEnabled()
def test_review_confirms_selected_candidate(qtbot):
    controller = Controller(); page = ReviewPage(controller); qtbot.addWidget(page)
    page.show_case("f1", Path("photo.jpg"), [("p1", "张小明", .62), ("p2", "李小红", .40)])
    page.candidates.setCurrentRow(0); qtbot.mouseClick(page.confirm_button, Qt.LeftButton)
    assert controller.confirmed == ("f1", "p1")
def test_results_loads_people_and_photos(qtbot):
    page = ResultsPage(Results()); qtbot.addWidget(page); page.select_task("t1"); page.select_person("p1")
    qtbot.waitUntil(lambda: page.photos_list.count() == 2)
    assert page.people_list.count() == 1 and page.photos_list.count() == 2

def test_results_shows_thumbnail_grid_and_placeholder_for_missing_photo(qtbot, tmp_path):
    existing = tmp_path / "existing.png"
    pixmap = QPixmap(40, 30); pixmap.fill(Qt.red); assert pixmap.save(str(existing))
    page = ResultsPage(Results([existing, tmp_path / "missing.png"])); qtbot.addWidget(page)
    page.select_task("t1"); page.select_person("p1")
    qtbot.waitUntil(lambda: page.photos_list.count() == 2)
    assert page.photos_list.viewMode() == QListView.IconMode
    assert not page.photos_list.item(0).icon().isNull()
    assert not page.photos_list.item(1).icon().isNull()
    qtbot.waitUntil(lambda: page.photos_list.item(1).data(Qt.UserRole + 1) is False)
    assert "不可用" in page.photos_list.item(1).toolTip()

def test_review_lists_pending_photos_and_confirms_selected_item(qtbot, tmp_path):
    cases = [
        {"face_id":"f1", "photo_path":tmp_path / "missing-1.jpg", "box":[0,0,1,1], "candidates":[("p1", "张小明", .62)]},
        {"face_id":"f2", "photo_path":tmp_path / "missing-2.jpg", "box":[0,0,1,1], "candidates":[("p2", "李小红", .71)]},
    ]
    controller = ReviewController(cases); page = ReviewPage(controller); qtbot.addWidget(page)
    page.load_next()
    qtbot.waitUntil(lambda: page.reviews_list.count() == 2)
    assert page.reviews_list.count() == 2
    assert not page.reviews_list.item(0).icon().isNull()
    page.reviews_list.setCurrentRow(1)
    assert page.face_id == "f2" and page.candidates.item(0).data(Qt.UserRole) == "p2"
    qtbot.mouseClick(page.confirm_button, Qt.LeftButton)
    assert controller.confirmed == ("f2", "p2")
    qtbot.waitUntil(lambda: page.reviews_list.count() == 1)
    assert page.reviews_list.count() == 1 and page.face_id == "f1"

def test_results_returns_before_slow_thumbnail_decode_finishes(qtbot, monkeypatch, tmp_path):
    release = threading.Event()
    def slow_read(_path: Path, size: QSize):
        release.wait(timeout=1)
        return QImage(size, QImage.Format_RGB32), True
    monkeypatch.setattr(thumbnails, "read_thumbnail_image", slow_read)
    timer = threading.Timer(.3, release.set); timer.start()
    page = ResultsPage(Results([tmp_path / "large.jpg"])); qtbot.addWidget(page); page.select_task("t1")
    started = time.monotonic(); page.select_person("p1"); elapsed = time.monotonic() - started
    assert elapsed < .15 and page.photos_list.count() == 0
    qtbot.waitUntil(lambda: page.photos_list.count() == 1)
    release.set(); timer.join()

def test_review_returns_before_slow_thumbnail_decode_finishes(qtbot, monkeypatch, tmp_path):
    release = threading.Event()
    def slow_read(_path: Path, size: QSize):
        release.wait(timeout=1)
        return QImage(size, QImage.Format_RGB32), True
    monkeypatch.setattr(thumbnails, "read_thumbnail_image", slow_read)
    cases = [{"face_id":"f1", "photo_path":tmp_path / "large.jpg", "box":[0,0,1,1], "candidates":[("p1", "张小明", .62)]}]
    timer = threading.Timer(.3, release.set); timer.start()
    page = ReviewPage(ReviewController(cases)); qtbot.addWidget(page)
    started = time.monotonic(); page.load_next(); elapsed = time.monotonic() - started
    assert elapsed < .15 and page.reviews_list.count() == 0
    qtbot.waitUntil(lambda: page.reviews_list.count() == 1)
    release.set(); timer.join()

def test_double_click_result_opens_original_image(qtbot, monkeypatch, tmp_path):
    path = tmp_path / "result.jpg"; opened = []
    monkeypatch.setattr(results_page_module, "open_image", lambda value, _parent: opened.append(Path(value)))
    page = ResultsPage(Results([path])); qtbot.addWidget(page); page.select_task("t1"); page.select_person("p1")
    qtbot.waitUntil(lambda: page.photos_list.count() == 1)
    page.photos_list.itemDoubleClicked.emit(page.photos_list.item(0))
    assert opened == [path]

def test_double_click_review_opens_original_image(qtbot, monkeypatch, tmp_path):
    path = tmp_path / "review.jpg"; opened = []
    cases = [{"face_id":"f1", "photo_path":path, "box":[0,0,1,1], "candidates":[]}]
    monkeypatch.setattr(review_page_module, "open_image", lambda value, _parent: opened.append(Path(value)))
    page = ReviewPage(ReviewController(cases)); qtbot.addWidget(page); page.load_next()
    qtbot.waitUntil(lambda: page.reviews_list.count() == 1)
    page.reviews_list.itemDoubleClicked.emit(page.reviews_list.item(0))
    assert opened == [path]

def test_results_adds_large_photo_collection_in_ui_batches(qtbot):
    photos = [Path(f"{index}.jpg") for index in range(500)]
    page = ResultsPage(Results(photos)); qtbot.addWidget(page); page.select_task("t1")
    page.select_person("p1")
    assert page.photos_list.count() < 500
    qtbot.waitUntil(lambda: page.photos_list.count() == 500, timeout=5000)

def test_review_adds_large_pending_collection_in_ui_batches(qtbot):
    cases = [
        {"face_id":f"f{index}", "photo_path":Path(f"{index}.jpg"), "box":[0,0,1,1], "candidates":[]}
        for index in range(500)
    ]
    page = ReviewPage(ReviewController(cases)); qtbot.addWidget(page); page.load_next()
    assert page.reviews_list.count() < 500
    qtbot.waitUntil(lambda: page.reviews_list.count() == 500, timeout=5000)
