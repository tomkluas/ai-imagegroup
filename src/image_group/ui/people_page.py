from collections import deque
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from image_group.ui.image_actions import open_image
from image_group.ui.thumbnails import AsyncThumbnailLoader, placeholder_pixmap


class PeoplePage(QWidget):
    people_changed = Signal()
    thumbnail_size = QSize(160, 120)
    batch_size = 24
    batch_delay_ms = 8

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.reference_batch = deque()
        self.reference_batch_generation = 0
        self.thumbnail_loader = AsyncThumbnailLoader(self)
        self.thumbnail_loader.loaded.connect(self._thumbnail_loaded)
        self.loading_pixmap = placeholder_pixmap(self.thumbnail_size, "正在加载")

        layout = QVBoxLayout(self)
        title = QLabel("学生与参考照片")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        row = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入学生姓名")
        self.add_button = QPushButton("新增学生")
        self.add_button.setProperty("primaryAction", True)
        row.addWidget(self.name_edit)
        row.addWidget(self.add_button)
        layout.addLayout(row)

        body = QHBoxLayout()
        self.people_list = QListWidget()
        self.people_list.setObjectName("peopleList")
        self.references = QListWidget()
        self.references.setObjectName("referenceGrid")
        self.references.setViewMode(QListView.IconMode)
        self.references.setIconSize(self.thumbnail_size)
        self.references.setGridSize(QSize(190, 165))
        self.references.setResizeMode(QListView.Adjust)
        self.references.setWordWrap(True)
        body.addWidget(self.people_list, 1)
        body.addWidget(self.references, 3)
        layout.addLayout(body)

        actions = QHBoxLayout()
        self.import_button = QPushButton("添加参考照片")
        self.bulk_button = QPushButton("批量导入姓名文件夹")
        self.rename_button = QPushButton("重命名")
        self.delete_ref_button = QPushButton("删除参考照")
        self.delete_button = QPushButton("删除学生")
        self.delete_ref_button.setProperty("dangerAction", True)
        self.delete_button.setProperty("dangerAction", True)
        for button in (
            self.import_button,
            self.bulk_button,
            self.rename_button,
            self.delete_ref_button,
            self.delete_button,
        ):
            actions.addWidget(button)
        layout.addLayout(actions)
        layout.addWidget(QLabel("建议每位学生提供 3～5 张清晰正脸或轻微侧脸照片。"))

        self.add_button.clicked.connect(self._add_person)
        self.import_button.clicked.connect(self._import)
        self.bulk_button.clicked.connect(self._bulk)
        self.rename_button.clicked.connect(self._rename)
        self.delete_button.clicked.connect(self._delete)
        self.delete_ref_button.clicked.connect(self._delete_reference)
        self.people_list.itemSelectionChanged.connect(self._load_references)
        self.references.itemDoubleClicked.connect(self._open_reference)
        self.refresh()

    def _people(self):
        if hasattr(self.service, "list_people"):
            return self.service.list_people()
        return self.service.people.list_all()

    def _selected_id(self):
        item = self.people_list.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _add_person(self):
        try:
            self.service.create_person(self.name_edit.text())
            self.name_edit.clear()
            self.refresh()
            self.people_changed.emit()
        except Exception as exc:
            QMessageBox.warning(self, "无法新增", str(exc))

    def _import(self):
        person_id = self._selected_id()
        if not person_id:
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择参考照片", "", "图片 (*.jpg *.jpeg *.png *.bmp *.webp)"
        )
        for path in paths:
            try:
                self.service.import_reference(person_id, Path(path))
            except Exception as exc:
                QMessageBox.warning(self, "导入失败", f"{path}\n{exc}")
        self._load_references()
        self.people_changed.emit()

    def _bulk(self):
        root = QFileDialog.getExistingDirectory(self, "选择包含姓名子文件夹的目录")
        if root:
            result = self.service.bulk_import(Path(root))
            self.refresh()
            self.people_changed.emit()
            QMessageBox.information(
                self,
                "批量导入",
                f"已导入 {result.imported_count} 张，失败 {len(result.failures)} 张",
            )

    def _rename(self):
        person_id = self._selected_id()
        if person_id and self.name_edit.text().strip():
            self.service.rename_person(person_id, self.name_edit.text())
            self.refresh()
            self.people_changed.emit()

    def _delete(self):
        person_id = self._selected_id()
        if person_id and QMessageBox.question(
            self, "确认删除", "将删除此学生的参考照与分类副本，原始照片不受影响。"
        ) == QMessageBox.Yes:
            self.service.delete_person(person_id)
            self.refresh()
            self.people_changed.emit()

    def _delete_reference(self):
        item = self.references.currentItem()
        if item:
            self.service.delete_reference(item.data(Qt.UserRole))
            self._load_references()
            self.people_changed.emit()

    def _load_references(self):
        self.thumbnail_loader.begin_batch()
        self.reference_batch_generation += 1
        self.references.clear()
        person_id = self._selected_id()
        if not person_id or not hasattr(self.service, "database"):
            return
        self.reference_batch = deque(
            self.service.database.execute(
                "SELECT id,managed_path FROM reference_photos "
                "WHERE person_id=? ORDER BY created_at",
                (person_id,),
            )
        )
        generation = self.reference_batch_generation
        QTimer.singleShot(0, lambda: self._append_reference_batch(generation))

    def _append_reference_batch(self, generation):
        if generation != self.reference_batch_generation:
            return
        for _ in range(min(self.batch_size, len(self.reference_batch))):
            row = self.reference_batch.popleft()
            reference_id, value = row
            path = Path(value)
            index = self.references.count()
            item = QListWidgetItem(QIcon(self.loading_pixmap), path.name)
            item.setData(Qt.UserRole, reference_id)
            item.setData(Qt.UserRole + 1, str(path))
            item.setToolTip(f"正在加载：{path}")
            self.references.addItem(item)
            self.thumbnail_loader.request(
                path, self.thumbnail_size, (index, reference_id, str(path))
            )
        if self.reference_batch:
            QTimer.singleShot(
                self.batch_delay_ms, lambda: self._append_reference_batch(generation)
            )

    def _thumbnail_loaded(self, request_key, image, available):
        index, reference_id, path = request_key
        if index >= self.references.count():
            return
        item = self.references.item(index)
        if item.data(Qt.UserRole) != reference_id or item.data(Qt.UserRole + 1) != path:
            return
        pixmap = QPixmap.fromImage(image) if available else placeholder_pixmap(
            self.thumbnail_size
        )
        item.setIcon(QIcon(pixmap))
        item.setToolTip(path if available else f"图片不可用：{path}")

    def _open_reference(self, item):
        open_image(item.data(Qt.UserRole + 1), self)

    def refresh(self):
        self.people_list.clear()
        for person in self._people():
            item = QListWidgetItem(person.display_name)
            item.setData(Qt.UserRole, person.id)
            self.people_list.addItem(item)

    def person_names(self):
        return [self.people_list.item(i).text() for i in range(self.people_list.count())]
