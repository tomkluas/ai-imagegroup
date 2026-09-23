from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ReviewPage(QWidget):
    def __init__(self, controller):
        super().__init__(); self.controller = controller; self.face_id = None
        layout = QVBoxLayout(self); layout.addWidget(QLabel("待人工确认")); self.photo_label = QLabel("暂无待确认照片"); self.photo_label.setAlignment(Qt.AlignCenter); self.photo_label.setMinimumHeight(360); layout.addWidget(self.photo_label)
        self.candidates = QListWidget(); layout.addWidget(self.candidates); row = QHBoxLayout(); self.confirm_button = QPushButton("确认姓名"); self.reject_button = QPushButton("不是这些人"); self.skip_button = QPushButton("跳过")
        for button in (self.confirm_button, self.reject_button, self.skip_button): row.addWidget(button)
        layout.addLayout(row); self.confirm_button.clicked.connect(self.confirm); self.reject_button.clicked.connect(self.reject); self.skip_button.clicked.connect(self.skip)
    def load_next(self):
        cases = self.controller.pending_reviews() if hasattr(self.controller, "pending_reviews") else []
        if cases: self.show_case(cases[0]["face_id"], cases[0]["photo_path"], cases[0]["candidates"])
        else: self.face_id = None; self.photo_label.setText("暂无待确认照片"); self.photo_label.setPixmap(QPixmap()); self.candidates.clear()
    def show_case(self, face_id, photo_path: Path, candidates):
        self.face_id = face_id; pixmap = QPixmap(str(photo_path)); self.photo_label.setPixmap(pixmap.scaled(900, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation)); self.photo_label.setToolTip(str(photo_path)); self.candidates.clear()
        for person_id, name, score in candidates:
            item = QListWidgetItem(f"{name}  {score:.0%}"); item.setData(Qt.UserRole, person_id); self.candidates.addItem(item)
        if self.candidates.count(): self.candidates.setCurrentRow(0)
    def confirm(self):
        item = self.candidates.currentItem()
        if item and self.face_id: self.controller.confirm(self.face_id, item.data(Qt.UserRole)); self.load_next()
    def reject(self):
        if self.face_id and hasattr(self.controller, "reject"): self.controller.reject(self.face_id); self.load_next()
    def skip(self):
        if self.face_id and hasattr(self.controller, "skip"): self.controller.skip(self.face_id); self.load_next()
