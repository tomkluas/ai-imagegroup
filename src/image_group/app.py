from __future__ import annotations
import os, sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from image_group.hardware.profile import HardwareProfiler
from image_group.people.service import PeopleService
from image_group.recognition.opencv_backend import OpenCvRecognitionBackend
from image_group.storage.database import Database
from image_group.storage.repositories import PersonRepository
from image_group.ui.main_window import MainWindow
from image_group.ui.people_page import PeoplePage
from image_group.ui.settings_page import SettingsPage

def resource_root() -> Path:
    bundle = getattr(sys, "_MEIPASS", None)
    return Path(bundle) if bundle else Path(__file__).parents[2]
def default_data_root() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ImageGroup"
def build_main_window(data_root: Path, model_root: Path) -> MainWindow:
    data_root = Path(data_root); data_root.mkdir(parents=True, exist_ok=True)
    database = Database(data_root / "data.db"); database.migrate()
    backend = OpenCvRecognitionBackend(model_root)
    people = PeopleService(database, PersonRepository(database), data_root / "reference", backend)
    window = MainWindow(PeoplePage(people), SettingsPage(HardwareProfiler()))
    window.database = database
    return window
def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = build_main_window(default_data_root(), resource_root() / "resources" / "models")
    window.show(); return app.exec()
if __name__ == "__main__": raise SystemExit(main())
