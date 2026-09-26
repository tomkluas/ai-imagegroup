import os
from collections import deque
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
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

from image_group.ui.image_actions import open_image
from image_group.ui.thumbnails import AsyncThumbnailLoader, placeholder_pixmap


class ResultsPage(QWidget):
    thumbnail_size = QSize(160, 120)
    batch_size = 24
    batch_delay_ms = 8

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.task_id = None
        self.output_root = None
        self.photo_batch = deque()
        self.photo_batch_generation = 0
        self.thumbnail_loader = AsyncThumbnailLoader(self)
        self.thumbnail_loader.loaded.connect(self._thumbnail_loaded)
        self.loading_pixmap = placeholder_pixmap(self.thumbnail_size, "正在加载")

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
        self.photos_list.itemDoubleClicked.connect(self._open_photo)
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
        self.thumbnail_loader.begin_batch()
        self.photo_batch_generation += 1
        self.photo_batch.clear()
        self.task_id = task_id
        self.people_list.clear()
        self.photos_list.clear()
        for person in self.service.list_people(task_id):
            item = QListWidgetItem(f"{person['name']} ({person['count']})")
            item.setData(Qt.UserRole, person["id"])
            self.people_list.addItem(item)

    def select_person(self, person_id):
        self.thumbnail_loader.begin_batch()
        self.photo_batch_generation += 1
        self.photos_list.clear()
        self.photo_batch = deque(self.service.list_photos(self.task_id, person_id))
        generation = self.photo_batch_generation
        QTimer.singleShot(0, lambda: self._append_photo_batch(generation))

    def _append_photo_batch(self, generation):
        if generation != self.photo_batch_generation:
            return
        for _ in range(min(self.batch_size, len(self.photo_batch))):
            value = self.photo_batch.popleft()
            path = Path(value)
            index = self.photos_list.count()
            item = QListWidgetItem(QIcon(self.loading_pixmap), path.name)
            item.setData(Qt.UserRole, str(path))
            item.setData(Qt.UserRole + 1, None)
            item.setToolTip(f"正在加载：{path}")
            self.photos_list.addItem(item)
            self.thumbnail_loader.request(path, self.thumbnail_size, (index, str(path)))
        if self.photo_batch:
            QTimer.singleShot(
                self.batch_delay_ms, lambda: self._append_photo_batch(generation)
            )

    def _thumbnail_loaded(self, request_key, image, available):
        index, path = request_key
        if index >= self.photos_list.count():
            return
        item = self.photos_list.item(index)
        if item.data(Qt.UserRole) != path:
            return
        pixmap = QPixmap.fromImage(image) if available else placeholder_pixmap(
            self.thumbnail_size
        )
        item.setIcon(QIcon(pixmap))
        item.setData(Qt.UserRole + 1, available)
        item.setToolTip(path if available else f"图片不可用：{path}")

    def _person_changed(self):
        item = self.people_list.currentItem()
        if item:
            self.select_person(item.data(Qt.UserRole))

    def _open(self):
        if self.output_root and os.name == "nt":
            os.startfile(self.output_root)

    def _open_photo(self, item):
        open_image(item.data(Qt.UserRole), self)
