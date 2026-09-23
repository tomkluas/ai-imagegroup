from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class PlaceholderPage(QWidget):
    def __init__(self, title, text):
        super().__init__(); layout = QVBoxLayout(self); layout.addWidget(QLabel(title)); body = QLabel(text); body.setWordWrap(True); layout.addWidget(body); layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self, people_page, settings_page, new_task_page=None, review_page=None, results_page=None):
        super().__init__(); self.setWindowTitle("园区照片分类助手"); self.resize(1100, 720)
        root = QWidget(); layout = QHBoxLayout(root); self.navigation = QListWidget(); self.navigation.setFixedWidth(170); self.navigation.addItems(["小朋友管理", "新建分类任务", "待人工确认", "分类结果", "设置"]); layout.addWidget(self.navigation)
        self.pages = QStackedWidget(); layout.addWidget(self.pages, 1); self.people_page = people_page; self.new_task_page = new_task_page; self.review_page = review_page; self.results_page = results_page
        self.pages.addWidget(people_page); self.pages.addWidget(new_task_page or PlaceholderPage("新建分类任务", "选择照片和输出目录后开始分类。")); self.pages.addWidget(review_page or PlaceholderPage("待人工确认", "不确定的人脸会出现在这里。")); self.pages.addWidget(results_page or PlaceholderPage("分类结果", "按小朋友浏览分类结果。")); self.pages.addWidget(settings_page)
        self.navigation.currentRowChanged.connect(self._navigate); self.navigation.setCurrentRow(0); self.setCentralWidget(root); self.setStyleSheet("QMainWindow{background:#f5f7fb} QListWidget{font-size:15px;padding:8px} QLabel#pageTitle{font-size:22px;font-weight:600} QPushButton{padding:7px 14px}")
    def _navigate(self, index):
        self.pages.setCurrentIndex(index)
        if index == 2 and self.review_page: self.review_page.load_next()
        if index == 3 and self.results_page: self.results_page.refresh_tasks()
