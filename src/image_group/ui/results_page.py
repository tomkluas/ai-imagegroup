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


class ResultsPage(QWidget):
    def __init__(self, service):
        super().__init__(); self.service=service; self.task_id=None; layout=QVBoxLayout(self); layout.addWidget(QLabel("分类结果")); body=QHBoxLayout(); self.people_list=QListWidget(); self.photos_list=QListWidget(); body.addWidget(self.people_list,1); body.addWidget(self.photos_list,3); layout.addLayout(body); self.open_button=QPushButton("打开输出文件夹"); layout.addWidget(self.open_button); self.people_list.itemSelectionChanged.connect(self._person_changed)
    def select_task(self, task_id):
        self.task_id=task_id; self.people_list.clear(); self.photos_list.clear()
        for person in self.service.list_people(task_id):
            item=QListWidgetItem(f"{person['name']} ({person['count']})"); item.setData(Qt.UserRole,person['id']); self.people_list.addItem(item)
    def select_person(self, person_id):
        self.photos_list.clear()
        for path in self.service.list_photos(self.task_id,person_id): self.photos_list.addItem(str(path))
    def _person_changed(self):
        item=self.people_list.currentItem()
        if item: self.select_person(item.data(Qt.UserRole))
