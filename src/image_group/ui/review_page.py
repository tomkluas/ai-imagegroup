from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
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


class ReviewPage(QWidget):
    thumbnail_size = QSize(150, 110)
    preview_size = QSize(720, 440)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.face_id = None
        self.review_cases = {}
        self.current_photo_path = None
        self.list_loader = AsyncThumbnailLoader(self)
        self.preview_loader = AsyncThumbnailLoader(self, max_workers=1, cache_limit=32)
        self.list_loader.loaded.connect(self._list_thumbnail_loaded)
        self.preview_loader.loaded.connect(self._preview_loaded)
        self.loading_thumbnail = placeholder_pixmap(self.thumbnail_size, "正在加载")
        self.loading_preview = placeholder_pixmap(self.preview_size, "正在加载")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("待人工确认"))
        body = QHBoxLayout()

        self.reviews_list = QListWidget()
        self.reviews_list.setViewMode(QListView.IconMode)
        self.reviews_list.setIconSize(self.thumbnail_size)
        self.reviews_list.setGridSize(QSize(180, 155))
        self.reviews_list.setResizeMode(QListView.Adjust)
        self.reviews_list.setWordWrap(True)
        body.addWidget(self.reviews_list, 2)

        details = QVBoxLayout()
        self.photo_label = QLabel("暂无待确认照片")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setMinimumHeight(360)
        details.addWidget(self.photo_label, 3)
        details.addWidget(QLabel("请选择最符合的姓名："))
        self.candidates = QListWidget()
        details.addWidget(self.candidates, 1)

        row = QHBoxLayout()
        self.confirm_button = QPushButton("确认姓名")
        self.reject_button = QPushButton("不是这些人")
        self.skip_button = QPushButton("跳过")
        for button in (self.confirm_button, self.reject_button, self.skip_button):
            row.addWidget(button)
        details.addLayout(row)
        body.addLayout(details, 3)
        layout.addLayout(body)

        self.reviews_list.currentItemChanged.connect(self._review_selected)
        self.reviews_list.itemDoubleClicked.connect(self._open_review_photo)
        self.confirm_button.clicked.connect(self.confirm)
        self.reject_button.clicked.connect(self.reject)
        self.skip_button.clicked.connect(self.skip)

    def load_next(self):
        self.list_loader.begin_batch()
        self.preview_loader.begin_batch()
        cases = self.controller.pending_reviews() if hasattr(self.controller, "pending_reviews") else []
        self.review_cases = {case["face_id"]: case for case in cases}
        self.reviews_list.blockSignals(True)
        self.reviews_list.clear()
        for index, case in enumerate(cases, 1):
            path = Path(case["photo_path"])
            item = QListWidgetItem(QIcon(self.loading_thumbnail), f"{path.name}\n待确认 {index}")
            item.setData(Qt.UserRole, case["face_id"])
            item.setData(Qt.UserRole + 1, str(path))
            item.setToolTip(f"正在加载：{path}")
            self.reviews_list.addItem(item)
            self.list_loader.request(
                path, self.thumbnail_size, (index - 1, case["face_id"], str(path))
            )
        self.reviews_list.blockSignals(False)

        if self.reviews_list.count():
            self.reviews_list.setCurrentRow(0)
        else:
            self._clear_details()

    def _review_selected(self, current, _previous=None):
        if current is None:
            return
        case = self.review_cases.get(current.data(Qt.UserRole))
        if case:
            self.show_case(case["face_id"], Path(case["photo_path"]), case["candidates"])

    def _clear_details(self):
        self.face_id = None
        self.current_photo_path = None
        self.photo_label.setText("暂无待确认照片")
        self.photo_label.setPixmap(QPixmap())
        self.candidates.clear()

    def show_case(self, face_id, photo_path: Path, candidates):
        self.face_id = face_id
        self.current_photo_path = str(photo_path)
        self.preview_loader.begin_batch()
        self.photo_label.setPixmap(self.loading_preview)
        self.photo_label.setToolTip(f"正在加载：{photo_path}")
        self.preview_loader.request(
            photo_path, self.preview_size, (face_id, self.current_photo_path)
        )
        self.candidates.clear()
        for person_id, name, score in candidates:
            item = QListWidgetItem(f"{name}  {score:.0%}")
            item.setData(Qt.UserRole, person_id)
            self.candidates.addItem(item)
        if self.candidates.count():
            self.candidates.setCurrentRow(0)

    def _list_thumbnail_loaded(self, request_key, image, available):
        index, face_id, path = request_key
        if index >= self.reviews_list.count():
            return
        item = self.reviews_list.item(index)
        if item.data(Qt.UserRole) != face_id or item.data(Qt.UserRole + 1) != path:
            return
        pixmap = QPixmap.fromImage(image) if available else placeholder_pixmap(
            self.thumbnail_size
        )
        item.setIcon(QIcon(pixmap))
        item.setToolTip(path if available else f"图片不可用：{path}")

    def _preview_loaded(self, request_key, image, available):
        face_id, path = request_key
        if self.face_id != face_id or self.current_photo_path != path:
            return
        pixmap = QPixmap.fromImage(image) if available else placeholder_pixmap(
            self.preview_size
        )
        self.photo_label.setPixmap(pixmap)
        self.photo_label.setToolTip(path if available else f"图片不可用：{path}")

    def confirm(self):
        item = self.candidates.currentItem()
        if item and self.face_id:
            self.controller.confirm(self.face_id, item.data(Qt.UserRole))
            self.load_next()

    def reject(self):
        if self.face_id and hasattr(self.controller, "reject"):
            self.controller.reject(self.face_id)
            self.load_next()

    def skip(self):
        if self.face_id and hasattr(self.controller, "skip"):
            self.controller.skip(self.face_id)
            self.load_next()

    def _open_review_photo(self, item):
        open_image(item.data(Qt.UserRole + 1), self)
