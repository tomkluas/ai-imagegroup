from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PeoplePage(QWidget):
    people_changed = Signal()
    def __init__(self, service):
        super().__init__(); self.service = service
        layout = QVBoxLayout(self); title = QLabel("小朋友与参考照片"); title.setObjectName("pageTitle"); layout.addWidget(title)
        row = QHBoxLayout(); self.name_edit = QLineEdit(); self.name_edit.setPlaceholderText("输入小朋友姓名"); self.add_button = QPushButton("新增小朋友")
        row.addWidget(self.name_edit); row.addWidget(self.add_button); layout.addLayout(row)
        body = QHBoxLayout(); self.people_list = QListWidget(); self.references = QListWidget(); self.preview = QLabel("选择参考照片预览"); self.preview.setAlignment(Qt.AlignCenter); self.preview.setMinimumSize(280, 220)
        body.addWidget(self.people_list, 1); body.addWidget(self.references, 1); body.addWidget(self.preview, 2); layout.addLayout(body)
        actions = QHBoxLayout(); self.import_button = QPushButton("添加参考照片"); self.bulk_button = QPushButton("批量导入姓名文件夹"); self.rename_button = QPushButton("重命名"); self.delete_ref_button = QPushButton("删除参考照"); self.delete_button = QPushButton("删除小朋友")
        for button in (self.import_button, self.bulk_button, self.rename_button, self.delete_ref_button, self.delete_button): actions.addWidget(button)
        layout.addLayout(actions); layout.addWidget(QLabel("建议每位小朋友提供 3～5 张清晰正脸或轻微侧脸照片。"))
        self.add_button.clicked.connect(self._add_person); self.import_button.clicked.connect(self._import); self.bulk_button.clicked.connect(self._bulk); self.rename_button.clicked.connect(self._rename); self.delete_button.clicked.connect(self._delete); self.delete_ref_button.clicked.connect(self._delete_reference)
        self.people_list.itemSelectionChanged.connect(self._load_references); self.references.itemSelectionChanged.connect(self._preview); self.refresh()

    def _people(self): return self.service.list_people() if hasattr(self.service, "list_people") else self.service.people.list_all()
    def _selected_id(self):
        item = self.people_list.currentItem(); return item.data(Qt.UserRole) if item else None
    def _add_person(self):
        try: self.service.create_person(self.name_edit.text()); self.name_edit.clear(); self.refresh(); self.people_changed.emit()
        except Exception as exc: QMessageBox.warning(self, "无法新增", str(exc))
    def _import(self):
        person_id = self._selected_id()
        if not person_id: return
        paths, _ = QFileDialog.getOpenFileNames(self, "选择参考照片", "", "图片 (*.jpg *.jpeg *.png *.bmp *.webp)")
        for path in paths:
            try: self.service.import_reference(person_id, Path(path))
            except Exception as exc: QMessageBox.warning(self, "导入失败", f"{path}\n{exc}")
        self._load_references(); self.people_changed.emit()
    def _bulk(self):
        root = QFileDialog.getExistingDirectory(self, "选择包含姓名子文件夹的目录")
        if root:
            result = self.service.bulk_import(Path(root)); self.refresh(); self.people_changed.emit(); QMessageBox.information(self, "批量导入", f"已导入 {result.imported_count} 张，失败 {len(result.failures)} 张")
    def _rename(self):
        person_id = self._selected_id()
        if person_id and self.name_edit.text().strip(): self.service.rename_person(person_id, self.name_edit.text()); self.refresh(); self.people_changed.emit()
    def _delete(self):
        person_id = self._selected_id()
        if person_id and QMessageBox.question(self, "确认删除", "将删除此小朋友的参考照与分类副本，原始照片不受影响。") == QMessageBox.Yes:
            self.service.delete_person(person_id); self.refresh(); self.people_changed.emit()
    def _delete_reference(self):
        item = self.references.currentItem()
        if item: self.service.delete_reference(item.data(Qt.UserRole)); self._load_references(); self.people_changed.emit()
    def _load_references(self):
        self.references.clear(); person_id = self._selected_id()
        if not person_id or not hasattr(self.service, "database"): return
        for row in self.service.database.execute("SELECT id,managed_path FROM reference_photos WHERE person_id=? ORDER BY created_at", (person_id,)):
            item = QListWidgetItem(Path(row[1]).name); item.setData(Qt.UserRole, row[0]); item.setData(Qt.UserRole + 1, row[1]); self.references.addItem(item)
    def _preview(self):
        item = self.references.currentItem()
        if item: self.preview.setPixmap(QPixmap(item.data(Qt.UserRole + 1)).scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
    def refresh(self):
        self.people_list.clear()
        for person in self._people():
            item = QListWidgetItem(person.display_name); item.setData(Qt.UserRole, person.id); self.people_list.addItem(item)
    def person_names(self): return [self.people_list.item(i).text() for i in range(self.people_list.count())]
