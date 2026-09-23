from PySide6.QtWidgets import QComboBox, QLabel, QPushButton, QVBoxLayout, QWidget


class SettingsPage(QWidget):
    def __init__(self, profiler):
        super().__init__(); self.profiler = profiler; layout = QVBoxLayout(self)
        layout.addWidget(QLabel("性能与数据设置")); self.hardware_label = QLabel(); layout.addWidget(self.hardware_label)
        self.mode_combo = QComboBox(); self.mode_combo.addItems(["节能", "均衡", "高速"]); self.mode_combo.setCurrentText("均衡"); layout.addWidget(self.mode_combo)
        self.redetect_button = QPushButton("重新检测硬件"); self.redetect_button.clicked.connect(self.refresh); layout.addWidget(self.redetect_button); layout.addStretch(); self.refresh()
    def refresh(self):
        p = self.profiler.detect(); suffix = "（安全默认值）" if p.fallback else ""
        self.hardware_label.setText(f"{p.logical_cpus} 核 CPU · {p.total_memory_gb} GB 内存 · 当前可用 {p.available_memory_gb} GB{suffix}")

