from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox
class PeoplePage(QWidget):
    def __init__(self, service):
        super().__init__(); self.service = service
        layout = QVBoxLayout(self); title = QLabel("小朋友与参考照片"); title.setObjectName("pageTitle"); layout.addWidget(title)
        row = QHBoxLayout(); self.name_edit = QLineEdit(); self.name_edit.setPlaceholderText("输入小朋友姓名")
        self.add_button = QPushButton("新增小朋友"); row.addWidget(self.name_edit); row.addWidget(self.add_button); layout.addLayout(row)
        self.people_list = QListWidget(); layout.addWidget(self.people_list)
        self.hint = QLabel("建议每位小朋友提供 3～5 张清晰正脸或轻微侧脸照片。")
        self.hint.setWordWrap(True); layout.addWidget(self.hint)
        self.add_button.clicked.connect(self._add_person); self.refresh()
    def _people(self): return self.service.list_people() if hasattr(self.service, "list_people") else self.service.people.list_all()
    def _add_person(self):
        try:
            self.service.create_person(self.name_edit.text()); self.name_edit.clear(); self.refresh()
        except Exception as exc: QMessageBox.warning(self, "无法新增", str(exc))
    def refresh(self):
        self.people_list.clear()
        for person in self._people(): self.people_list.addItem(person.display_name)
    def person_names(self): return [self.people_list.item(i).text() for i in range(self.people_list.count())]

