from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class TaskWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, controller, args):
        super().__init__(); self.controller, self.args = controller, args

    @Slot()
    def run(self):
        try: self.finished.emit(self.controller.start(*self.args))
        except Exception as exc: self.failed.emit(str(exc))


class NewTaskPage(QWidget):
    progress_changed = Signal(int, int)

    def __init__(self, scanner, controller, people):
        super().__init__(); self.scanner, self.controller = scanner, controller; self.input_paths = []; self.output_directory = None; self.thread = None
        layout = QVBoxLayout(self); layout.addWidget(QLabel("新建分类任务")); self.name_edit = QLineEdit("照片分类任务"); layout.addWidget(self.name_edit)
        pick = QHBoxLayout(); self.folder_button = QPushButton("选择照片文件夹"); self.files_button = QPushButton("选择多张照片"); self.output_button = QPushButton("选择输出目录")
        for button in (self.folder_button, self.files_button, self.output_button): pick.addWidget(button)
        layout.addLayout(pick); self.input_label = QLabel("尚未选择照片"); self.output_label = QLabel("尚未选择输出目录"); layout.addWidget(self.input_label); layout.addWidget(self.output_label); layout.addWidget(QLabel("本次参与识别的小朋友"))
        self.people_list = QListWidget(); layout.addWidget(self.people_list); self.progress = QProgressBar(); self.progress.setVisible(False); layout.addWidget(self.progress)
        buttons = QHBoxLayout(); self.start_button = QPushButton("开始分类"); self.cancel_button = QPushButton("取消"); self.cancel_button.setEnabled(False); buttons.addWidget(self.start_button); buttons.addWidget(self.cancel_button); layout.addLayout(buttons); self.set_people(people)
        self.start_button.clicked.connect(self.start); self.cancel_button.clicked.connect(lambda: getattr(controller, "cancel", lambda: None)()); self.people_list.itemChanged.connect(self.refresh_validity); self.folder_button.clicked.connect(self.pick_folder); self.files_button.clicked.connect(self.pick_files); self.output_button.clicked.connect(self.pick_output); self.progress_changed.connect(self.update_progress)

    def set_people(self, people):
        selected = set(self.selected_people()); self.people_list.clear()
        for person_id, name in people:
            item = QListWidgetItem(name); item.setData(Qt.UserRole, person_id); item.setFlags(item.flags() | Qt.ItemIsUserCheckable); item.setCheckState(Qt.Checked if person_id in selected else Qt.Unchecked); self.people_list.addItem(item)
        self.refresh_validity()
    def pick_folder(self):
        path = QFileDialog.getExistingDirectory(self, "选择待分类照片文件夹")
        if path: self.set_input_paths([Path(path)])
    def pick_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择待分类照片", "", "图片 (*.jpg *.jpeg *.png *.bmp *.webp)")
        if paths: self.set_input_paths([Path(path) for path in paths])
    def pick_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path: self.set_output_directory(Path(path))
    def set_input_paths(self, paths): self.input_paths = [Path(p) for p in paths]; self.input_label.setText(f"已选择 {len(self.input_paths)} 个来源"); self.refresh_validity()
    def set_output_directory(self, path): self.output_directory = Path(path); self.output_label.setText(str(path)); self.refresh_validity()
    def selected_people(self): return [self.people_list.item(i).data(Qt.UserRole) for i in range(self.people_list.count()) if self.people_list.item(i).checkState() == Qt.Checked]
    def refresh_validity(self): self.start_button.setEnabled(bool(self.input_paths and self.output_directory and self.selected_people()) and self.thread is None)
    def start(self):
        self.progress.setVisible(True); self.start_button.setEnabled(False); self.cancel_button.setEnabled(True); self.thread = QThread(self); self.worker = TaskWorker(self.controller, (self.name_edit.text().strip(), self.input_paths, self.output_directory, self.selected_people())); self.worker.moveToThread(self.thread); self.thread.started.connect(self.worker.run); self.worker.finished.connect(self._done); self.worker.failed.connect(self._failed); self.worker.finished.connect(self.thread.quit); self.worker.failed.connect(self.thread.quit); self.thread.finished.connect(self._clear_thread); self.thread.start()
    def _done(self, _task_id): QMessageBox.information(self, "分类完成", "分类已完成，请查看人工确认和分类结果。")
    def _failed(self, message): QMessageBox.critical(self, "分类失败", message)
    def _clear_thread(self): self.thread.deleteLater(); self.thread = None; self.cancel_button.setEnabled(False); self.refresh_validity()
    def update_progress(self, completed, total): self.progress.setRange(0, total); self.progress.setValue(completed)
