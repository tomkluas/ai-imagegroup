from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QInputDialog, QListView

from image_group.hardware.profile import HardwareProfile
from image_group.ui import people_page as people_page_module
from image_group.ui.main_window import MainWindow
from image_group.ui.people_page import PeoplePage
from image_group.ui.settings_page import SettingsPage


@dataclass
class Person: id: str; display_name: str
class Service:
    def __init__(self): self.people = []
    def create_person(self, name):
        person = Person(str(len(self.people)), name); self.people.append(person); return person
    def list_people(self): return list(self.people)
    def rename_person(self, person_id, name):
        person = next(person for person in self.people if person.id == person_id)
        person.display_name = name
        return person
class Database:
    def __init__(self, rows): self.rows = rows
    def execute(self, _query, _parameters): return list(self.rows)
class Profiler:
    def detect(self): return HardwareProfile(2, 8, 4, False)

def test_add_person_refreshes_list(qtbot):
    service = Service(); page = PeoplePage(service); qtbot.addWidget(page); page.show()
    page.name_edit.setText("张小明"); qtbot.mouseClick(page.add_button, Qt.LeftButton)
    assert page.person_names() == ["张小明"]

def test_rename_prompts_with_current_name_and_keeps_person_selected(qtbot, monkeypatch):
    service = Service(); service.people = [Person("p1", "旧名字")]
    page = PeoplePage(service); qtbot.addWidget(page); page.people_list.setCurrentRow(0)
    prompts = []

    def get_text(_parent, title, label, _mode, value):
        prompts.append((title, label, value))
        return "新名字", True

    monkeypatch.setattr(QInputDialog, "getText", get_text)
    qtbot.mouseClick(page.rename_button, Qt.LeftButton)

    assert prompts == [("重命名学生", "请输入新的学生姓名：", "旧名字")]
    assert page.person_names() == ["新名字"]
    assert page.people_list.currentItem().data(Qt.UserRole) == "p1"
def test_main_window_has_five_navigation_items(qtbot):
    service = Service(); window = MainWindow(PeoplePage(service), SettingsPage(Profiler()))
    qtbot.addWidget(window)
    assert window.navigation.count() == 5
def test_settings_page_displays_detected_hardware(qtbot):
    page = SettingsPage(Profiler()); qtbot.addWidget(page)
    assert "2 核" in page.hardware_label.text() and "8 GB" in page.hardware_label.text()

def test_references_are_one_thumbnail_grid_without_separate_preview(qtbot, tmp_path):
    path = tmp_path / "reference.jpg"
    service = Service(); service.people = [Person("p1", "张小明")]
    service.database = Database([("r1", str(path))])
    page = PeoplePage(service); qtbot.addWidget(page); page.people_list.setCurrentRow(0)
    qtbot.waitUntil(lambda: page.references.count() == 1)
    assert page.references.viewMode() == QListView.IconMode
    assert page.references.count() == 1
    assert not hasattr(page, "preview")

def test_double_click_reference_opens_original_image(qtbot, monkeypatch, tmp_path):
    path = tmp_path / "reference.jpg"
    service = Service(); service.people = [Person("p1", "张小明")]
    service.database = Database([("r1", str(path))])
    opened = []
    monkeypatch.setattr(people_page_module, "open_image", lambda value, _parent: opened.append(Path(value)))
    page = PeoplePage(service); qtbot.addWidget(page); page.people_list.setCurrentRow(0)
    qtbot.waitUntil(lambda: page.references.count() == 1)
    page.references.itemDoubleClicked.emit(page.references.item(0))
    assert opened == [path]
