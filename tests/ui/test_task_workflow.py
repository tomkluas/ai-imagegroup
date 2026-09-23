from pathlib import Path
from PySide6.QtCore import Qt
from image_group.ui.new_task_page import NewTaskPage
from image_group.ui.review_page import ReviewPage
from image_group.ui.results_page import ResultsPage
class Scanner:
    def scan(self, paths): return type("Result", (), {"photos":[type("P", (), {"path": Path("a.jpg"), "size":12})()], "duplicates":[], "errors":[]})()
class Controller:
    def __init__(self): self.started = None; self.confirmed = None
    def start(self, name, paths, output, people): self.started = (name, paths, output, people)
    def confirm(self, face_id, person_id): self.confirmed = (face_id, person_id)
class Results:
    def list_tasks(self): return [{"id":"t1", "name":"今天", "count":2}]
    def list_people(self, task_id): return [{"id":"p1", "name":"张小明", "count":2}]
    def list_photos(self, task_id, person_id): return [Path("1.jpg"), Path("2.jpg")]

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
