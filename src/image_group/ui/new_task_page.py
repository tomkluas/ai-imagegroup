from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,QListWidget,QListWidgetItem,QProgressBar,QFileDialog
class NewTaskPage(QWidget):
    def __init__(self, scanner, controller, people):
        super().__init__(); self.scanner,self.controller=scanner,controller; self.input_paths=[]; self.output_directory=None
        layout=QVBoxLayout(self); layout.addWidget(QLabel("新建分类任务")); self.name_edit=QLineEdit("照片分类任务"); layout.addWidget(self.name_edit)
        pick=QHBoxLayout(); self.folder_button=QPushButton("选择照片文件夹"); self.files_button=QPushButton("选择多张照片"); self.output_button=QPushButton("选择输出目录")
        for button in (self.folder_button,self.files_button,self.output_button): pick.addWidget(button)
        layout.addLayout(pick); self.input_label=QLabel("尚未选择照片"); self.output_label=QLabel("尚未选择输出目录"); layout.addWidget(self.input_label); layout.addWidget(self.output_label)
        layout.addWidget(QLabel("本次参与识别的小朋友")); self.people_list=QListWidget(); layout.addWidget(self.people_list)
        for person_id,name in people:
            item=QListWidgetItem(name); item.setData(Qt.UserRole,person_id); item.setFlags(item.flags()|Qt.ItemIsUserCheckable); item.setCheckState(Qt.Unchecked); self.people_list.addItem(item)
        self.progress=QProgressBar(); self.progress.setVisible(False); layout.addWidget(self.progress); self.start_button=QPushButton("开始分类"); self.start_button.setEnabled(False); layout.addWidget(self.start_button)
        self.start_button.clicked.connect(self.start); self.people_list.itemChanged.connect(self.refresh_validity); self.folder_button.clicked.connect(self.pick_folder); self.files_button.clicked.connect(self.pick_files); self.output_button.clicked.connect(self.pick_output)
    def pick_folder(self):
        path=QFileDialog.getExistingDirectory(self,"选择待分类照片文件夹")
        if path:self.set_input_paths([Path(path)])
    def pick_files(self):
        paths,_=QFileDialog.getOpenFileNames(self,"选择待分类照片","","图片 (*.jpg *.jpeg *.png *.bmp *.webp)")
        if paths:self.set_input_paths([Path(path) for path in paths])
    def pick_output(self):
        path=QFileDialog.getExistingDirectory(self,"选择输出目录")
        if path:self.set_output_directory(Path(path))
    def set_input_paths(self,paths):self.input_paths=[Path(p) for p in paths];self.input_label.setText(f"已选择 {len(self.input_paths)} 个来源");self.refresh_validity()
    def set_output_directory(self,path):self.output_directory=Path(path);self.output_label.setText(str(path));self.refresh_validity()
    def selected_people(self):return [self.people_list.item(i).data(Qt.UserRole) for i in range(self.people_list.count()) if self.people_list.item(i).checkState()==Qt.Checked]
    def refresh_validity(self):self.start_button.setEnabled(bool(self.input_paths and self.output_directory and self.selected_people()))
    def start(self):self.progress.setVisible(True);self.controller.start(self.name_edit.text().strip(),self.input_paths,self.output_directory,self.selected_people())
    def update_progress(self,completed,total):self.progress.setRange(0,total);self.progress.setValue(completed)
