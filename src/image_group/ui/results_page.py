import os
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from image_group.ui.thumbnails import load_thumbnail


class ResultsPage(QWidget):
    thumbnail_size = QSize(160, 120)

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.task_id = None
        self.output_root = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("分类结果"))
        self.tasks = QComboBox()
        layout.addWidget(self.tasks)

        body = QHBoxLayout()
        self.people_list = QListWidget()
        self.photos_list = QListWidget()
        self.photos_list.setViewMode(QListView.IconMode)
        self.photos_list.setIconSize(self.thumbnail_size)
        self.photos_list.setGridSize(QSize(190, 165))
        self.photos_list.setResizeMode(QListView.Adjust)
        self.photos_list.setWordWrap(True)
        body.addWidget(self.people_list, 1)
        body.addWidget(self.photos_list, 3)
        layout.addLayout(body)

        self.open_button = QPushButton("打开输出文件夹")
        layout.addWidget(self.open_button)
        self.people_list.itemSelectionChanged.connect(self._person_changed)
        self.tasks.currentIndexChanged.connect(self._task_changed)
        self.open_button.clicked.connect(self._open)
        self.refresh_tasks()

    def refresh_tasks(self):
        self.tasks.blockSignals(True)
        self.tasks.clear()
        for task in self.service.list_tasks():
            self.tasks.addItem(f"{task['name']}（{task.get('status', '')}）", task)
        self.tasks.blockSignals(False)
        if self.tasks.count():
            self._task_changed(self.tasks.currentIndex())

    def _task_changed(self, index):
        if index >= 0:
            task = self.tasks.itemData(index)
            self.output_root = task.get("output_root")
            self.select_task(task["id"])

    def select_task(self, task_id):
        self.task_id = task_id
        self.people_list.clear()
        self.photos_list.clear()
        for person in self.service.list_people(task_id):
            item = QListWidgetItem(f"{person['name']} ({person['count']})")
            item.setData(Qt.UserRole, person["id"])
            self.people_list.addItem(item)

    def select_person(self, person_id):
        self.photos_list.clear()
        for value in self.service.list_photos(self.task_id, person_id):
            path = Path(value)
            pixmap, available = load_thumbnail(path, self.thumbnail_size)
            item = QListWidgetItem(QIcon(pixmap), path.name)
            item.setData(Qt.UserRole, str(path))
            item.setData(Qt.UserRole + 1, available)
            item.setToolTip(str(path) if available else f"图片不可用：{path}")
            self.photos_list.addItem(item)

    def _person_changed(self):
        item = self.people_list.currentItem()
        if item:
            self.select_person(item.data(Qt.UserRole))

    def _open(self):
        if self.output_root and os.name == "nt":
            os.startfile(self.output_root)
