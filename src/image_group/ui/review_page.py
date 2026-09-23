from pathlib import Path

from PySide6.QtCore import Qt
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
        super().__init__(); self.controller=controller; self.face_id=None; layout=QVBoxLayout(self); layout.addWidget(QLabel("待人工确认")); self.photo_label=QLabel("暂无待确认照片"); layout.addWidget(self.photo_label)
        self.candidates=QListWidget(); layout.addWidget(self.candidates); row=QHBoxLayout(); self.confirm_button=QPushButton("确认姓名"); self.reject_button=QPushButton("不是这些人"); self.skip_button=QPushButton("跳过"); row.addWidget(self.confirm_button); row.addWidget(self.reject_button); row.addWidget(self.skip_button); layout.addLayout(row); self.confirm_button.clicked.connect(self.confirm)
    def show_case(self, face_id, photo_path:Path, candidates):
        self.face_id=face_id; self.photo_label.setText(str(photo_path)); self.candidates.clear()
        for person_id,name,score in candidates:
            item=QListWidgetItem(f"{name}  {score:.0%}"); item.setData(Qt.UserRole,person_id); self.candidates.addItem(item)
    def confirm(self):
        item=self.candidates.currentItem()
        if item and self.face_id: self.controller.confirm(self.face_id,item.data(Qt.UserRole))

