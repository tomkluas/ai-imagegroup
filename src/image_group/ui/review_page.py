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

from image_group.ui.thumbnails import load_thumbnail


class ReviewPage(QWidget):
    thumbnail_size = QSize(150, 110)
    preview_size = QSize(720, 440)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.face_id = None
        self.review_cases = {}

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
        self.confirm_button.clicked.connect(self.confirm)
        self.reject_button.clicked.connect(self.reject)
        self.skip_button.clicked.connect(self.skip)

    def load_next(self):
        cases = self.controller.pending_reviews() if hasattr(self.controller, "pending_reviews") else []
        self.review_cases = {case["face_id"]: case for case in cases}
        self.reviews_list.blockSignals(True)
        self.reviews_list.clear()
        for index, case in enumerate(cases, 1):
            path = Path(case["photo_path"])
            pixmap, available = load_thumbnail(path, self.thumbnail_size)
            item = QListWidgetItem(QIcon(pixmap), f"{path.name}\n待确认 {index}")
            item.setData(Qt.UserRole, case["face_id"])
            item.setToolTip(str(path) if available else f"图片不可用：{path}")
            self.reviews_list.addItem(item)
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
        self.photo_label.setText("暂无待确认照片")
        self.photo_label.setPixmap(QPixmap())
        self.candidates.clear()

    def show_case(self, face_id, photo_path: Path, candidates):
        self.face_id = face_id
        pixmap, available = load_thumbnail(photo_path, self.preview_size)
        self.photo_label.setPixmap(pixmap)
        self.photo_label.setToolTip(str(photo_path) if available else f"图片不可用：{photo_path}")
        self.candidates.clear()
        for person_id, name, score in candidates:
            item = QListWidgetItem(f"{name}  {score:.0%}")
            item.setData(Qt.UserRole, person_id)
            self.candidates.addItem(item)
        if self.candidates.count():
            self.candidates.setCurrentRow(0)

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
