from dataclasses import dataclass
from PySide6.QtCore import Qt
from image_group.ui.main_window import MainWindow
from image_group.ui.people_page import PeoplePage
from image_group.ui.settings_page import SettingsPage
from image_group.hardware.profile import HardwareProfile

@dataclass
class Person: id: str; display_name: str
class Service:
    def __init__(self): self.people = []
    def create_person(self, name):
        person = Person(str(len(self.people)), name); self.people.append(person); return person
    def list_people(self): return list(self.people)
class Profiler:
    def detect(self): return HardwareProfile(2, 8, 4, False)

def test_add_person_refreshes_list(qtbot):
    service = Service(); page = PeoplePage(service); qtbot.addWidget(page); page.show()
    page.name_edit.setText("张小明"); qtbot.mouseClick(page.add_button, Qt.LeftButton)
    assert page.person_names() == ["张小明"]
def test_main_window_has_five_navigation_items(qtbot):
    service = Service(); window = MainWindow(PeoplePage(service), SettingsPage(Profiler()))
    qtbot.addWidget(window)
    assert window.navigation.count() == 5
def test_settings_page_displays_detected_hardware(qtbot):
    page = SettingsPage(Profiler()); qtbot.addWidget(page)
    assert "2 核" in page.hardware_label.text() and "8 GB" in page.hardware_label.text()
