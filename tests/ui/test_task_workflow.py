from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListView

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
    assert page.people_list.count() == 1 and page.photos_list.count() == 2

def test_results_shows_thumbnail_grid_and_placeholder_for_missing_photo(qtbot, tmp_path):
    existing = tmp_path / "existing.png"
    from PySide6.QtGui import QPixmap
    pixmap = QPixmap(40, 30); pixmap.fill(Qt.red); assert pixmap.save(str(existing))
    page = ResultsPage(Results([existing, tmp_path / "missing.png"])); qtbot.addWidget(page)
    page.select_task("t1"); page.select_person("p1")
    assert page.photos_list.viewMode() == QListView.IconMode
    assert not page.photos_list.item(0).icon().isNull()
    assert not page.photos_list.item(1).icon().isNull()
    assert "不可用" in page.photos_list.item(1).toolTip()

def test_review_lists_pending_photos_and_confirms_selected_item(qtbot, tmp_path):
    cases = [
        {"face_id":"f1", "photo_path":tmp_path / "missing-1.jpg", "box":[0,0,1,1], "candidates":[("p1", "张小明", .62)]},
        {"face_id":"f2", "photo_path":tmp_path / "missing-2.jpg", "box":[0,0,1,1], "candidates":[("p2", "李小红", .71)]},
    ]
    controller = ReviewController(cases); page = ReviewPage(controller); qtbot.addWidget(page)
    page.load_next()
    assert page.reviews_list.count() == 2
    assert not page.reviews_list.item(0).icon().isNull()
    page.reviews_list.setCurrentRow(1)
    assert page.face_id == "f2" and page.candidates.item(0).data(Qt.UserRole) == "p2"
    qtbot.mouseClick(page.confirm_button, Qt.LeftButton)
    assert controller.confirmed == ("f2", "p2")
    assert page.reviews_list.count() == 1 and page.face_id == "f1"
