from PySide6.QtWidgets import QComboBox, QLabel, QPushButton, QVBoxLayout, QWidget


class SettingsPage(QWidget):
    def __init__(self, profiler):
        super().__init__(); self.profiler = profiler; layout = QVBoxLayout(self); layout.addWidget(QLabel("性能与数据设置")); self.hardware_label = QLabel(); layout.addWidget(self.hardware_label)
        warning = QLabel("⚠ 当前识别阈值是保守默认值，尚未用本园区真实照片校准。首次使用请抽查结果；无法可靠识别的侧脸、遮挡、低头和远景会留给人工确认或忽略。"); warning.setWordWrap(True); warning.setStyleSheet("background:#fff3cd;color:#7a4b00;padding:12px;border-radius:6px"); layout.addWidget(warning)
        self.mode_combo = QComboBox(); self.mode_combo.addItems(["节能", "均衡", "高速"]); self.mode_combo.setCurrentText("均衡"); layout.addWidget(self.mode_combo); self.redetect_button = QPushButton("重新检测硬件"); self.redetect_button.clicked.connect(self.refresh); layout.addWidget(self.redetect_button); layout.addStretch(); self.refresh()
    def refresh(self):
        profile = self.profiler.detect(); suffix = "（安全默认值）" if profile.fallback else ""; self.hardware_label.setText(f"{profile.logical_cpus} 核 CPU · {profile.total_memory_gb} GB 内存 · 当前可用 {profile.available_memory_gb} GB{suffix}")
