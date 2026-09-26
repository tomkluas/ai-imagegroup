from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
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
        super().__init__()
        self.controller, self.args = controller, args

    @Slot()
    def run(self):
        try:
            self.finished.emit(self.controller.start(*self.args))
        except Exception as exc:
            self.failed.emit(str(exc))


class NewTaskPage(QWidget):
    progress_changed = Signal(int, int)

    def __init__(self, scanner, controller, people):
        super().__init__()
        self.scanner, self.controller = scanner, controller
        self.input_paths = []
        self.output_directory = None
        self.thread = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 10)
        layout.setSpacing(12)
        self.title = QLabel("新建分类任务")
        self.title.setObjectName("pageTitle")
        layout.addWidget(self.title)

        self.task_group = QGroupBox("任务设置")
        self.task_group.setObjectName("taskSettingsCard")
        task_layout = QVBoxLayout(self.task_group)
        task_layout.setContentsMargins(14, 18, 14, 14)
        task_layout.setSpacing(10)

        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        name_row.addWidget(self._field_label("任务名称"))
        self.name_edit = QLineEdit("照片分类任务")
        name_row.addWidget(self.name_edit, 1)
        task_layout.addLayout(name_row)

        source_row = QHBoxLayout()
        source_row.setSpacing(10)
        source_row.addWidget(self._field_label("照片来源"))
        self.folder_button = QPushButton("选择照片文件夹")
        self.files_button = QPushButton("选择多张照片")
        source_row.addWidget(self.folder_button)
        source_row.addWidget(self.files_button)
        source_row.addStretch(1)
        task_layout.addLayout(source_row)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        input_row.addWidget(self._field_label("已选照片"))
        self.input_label = QLabel("尚未选择照片")
        self.input_label.setObjectName("selectionSummary")
        self.input_label.setWordWrap(True)
        input_row.addWidget(self.input_label, 1)
        task_layout.addLayout(input_row)

        output_row = QHBoxLayout()
        output_row.setSpacing(10)
        output_row.addWidget(self._field_label("输出目录"))
        self.output_button = QPushButton("选择输出目录")
        output_row.addWidget(self.output_button)
        self.output_label = QLabel("尚未选择输出目录")
        self.output_label.setObjectName("selectionSummary")
        self.output_label.setWordWrap(True)
        output_row.addWidget(self.output_label, 1)
        task_layout.addLayout(output_row)
        layout.addWidget(self.task_group)

        people_header = QHBoxLayout()
        people_title = QLabel("本次参与识别的学生")
        people_title.setStyleSheet("font-weight:600;")
        people_header.addWidget(people_title)
        people_header.addStretch(1)
        people_header.addWidget(QLabel("请至少选择 1 名学生"))
        layout.addLayout(people_header)

        self.people_list = QListWidget()
        layout.addWidget(self.people_list, 1)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        self.start_button = QPushButton("开始分类")
        self.start_button.setMinimumWidth(160)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setMinimumWidth(120)
        self.cancel_button.setEnabled(False)
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)

        self.setStyleSheet(
            "QGroupBox#taskSettingsCard{font-weight:600;border:1px solid #d9dee8;"
            "border-radius:8px;margin-top:7px;background:#ffffff;}"
            "QGroupBox#taskSettingsCard::title{subcontrol-origin:margin;left:12px;"
            "padding:0 5px;}"
            "QLabel#selectionSummary{background:#f7f8fa;border:1px solid #e2e5ea;"
            "border-radius:5px;padding:6px;color:#4b5563;}"
        )

        self.set_people(people)
        self.start_button.clicked.connect(self.start)
        self.cancel_button.clicked.connect(
            lambda: getattr(controller, "cancel", lambda: None)()
        )
        self.people_list.itemChanged.connect(self.refresh_validity)
        self.folder_button.clicked.connect(self.pick_folder)
        self.files_button.clicked.connect(self.pick_files)
        self.output_button.clicked.connect(self.pick_output)
        self.progress_changed.connect(self.update_progress)

    @staticmethod
    def _field_label(text):
        label = QLabel(text)
        label.setFixedWidth(72)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return label

    def set_people(self, people):
        selected = set(self.selected_people())
        self.people_list.clear()
        for person_id, name in people:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, person_id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if person_id in selected else Qt.Unchecked)
            self.people_list.addItem(item)
        self.refresh_validity()

    def pick_folder(self):
        path = QFileDialog.getExistingDirectory(self, "选择待分类照片文件夹")
        if path:
            self.set_input_paths([Path(path)])

    def pick_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择待分类照片",
            "",
            "图片 (*.jpg *.jpeg *.png *.bmp *.webp)",
        )
        if paths:
            self.set_input_paths([Path(path) for path in paths])

    def pick_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.set_output_directory(Path(path))

    def set_input_paths(self, paths):
        self.input_paths = [Path(path) for path in paths]
        self.input_label.setText(f"已选择 {len(self.input_paths)} 个来源")
        self.input_label.setToolTip("\n".join(str(path) for path in self.input_paths))
        self.refresh_validity()

    def set_output_directory(self, path):
        self.output_directory = Path(path)
        self.output_label.setText(str(path))
        self.output_label.setToolTip(str(path))
        self.refresh_validity()

    def selected_people(self):
        return [
            self.people_list.item(index).data(Qt.UserRole)
            for index in range(self.people_list.count())
            if self.people_list.item(index).checkState() == Qt.Checked
        ]

    def refresh_validity(self):
        valid = self.input_paths and self.output_directory and self.selected_people()
        self.start_button.setEnabled(bool(valid) and self.thread is None)

    def start(self):
        self.progress.setVisible(True)
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        args = (
            self.name_edit.text().strip(),
            self.input_paths,
            self.output_directory,
            self.selected_people(),
        )
        self.thread = QThread(self)
        self.worker = TaskWorker(self.controller, args)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._done)
        self.worker.failed.connect(self._failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self._clear_thread)
        self.thread.start()

    def _done(self, _task_id):
        QMessageBox.information(self, "分类完成", "分类已完成，请查看人工确认和分类结果。")

    def _failed(self, message):
        QMessageBox.critical(self, "分类失败", message)

    def _clear_thread(self):
        self.thread.deleteLater()
        self.thread = None
        self.cancel_button.setEnabled(False)
        self.refresh_validity()

    def update_progress(self, completed, total):
        self.progress.setRange(0, total)
        self.progress.setValue(completed)
