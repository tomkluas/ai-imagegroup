from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from image_group.application import ClassificationController, ResultQueryService
from image_group.hardware.profile import HardwareProfiler
from image_group.people.adapter import BackendReferenceValidator
from image_group.people.service import PeopleService
from image_group.photos.io import ImageLoader
from image_group.recognition.opencv_backend import OpenCvRecognitionBackend
from image_group.storage.database import Database
from image_group.storage.repositories import PersonRepository
from image_group.tasks.scanner import PhotoScanner
from image_group.ui.main_window import MainWindow
from image_group.ui.new_task_page import NewTaskPage
from image_group.ui.people_page import PeoplePage
from image_group.ui.results_page import ResultsPage
from image_group.ui.review_page import ReviewPage
from image_group.ui.settings_page import SettingsPage


def resource_root():return Path(getattr(sys,"_MEIPASS",Path(__file__).parents[2]))
def default_data_root():return Path(os.environ.get("LOCALAPPDATA",Path.home()))/"ImageGroup"
def build_main_window(data_root:Path,model_root:Path):
    data_root=Path(data_root);data_root.mkdir(parents=True,exist_ok=True);db=Database(data_root/"data.db");db.migrate();backend=OpenCvRecognitionBackend(model_root)
    people=PeopleService(db,PersonRepository(db),data_root/"reference",BackendReferenceValidator(backend));controller=ClassificationController(db,backend,ImageLoader());query=ResultQueryService(db)
    person_options=[(p.id,p.display_name) for p in people.people.list_all()]
    window=MainWindow(PeoplePage(people),SettingsPage(HardwareProfiler()),NewTaskPage(PhotoScanner(),controller,person_options),ReviewPage(controller),ResultsPage(query));window.database=db;return window
def main():
    app=QApplication.instance() or QApplication(sys.argv);window=build_main_window(default_data_root(),resource_root()/"resources"/"models");window.show();return app.exec()
if __name__=="__main__":raise SystemExit(main())
