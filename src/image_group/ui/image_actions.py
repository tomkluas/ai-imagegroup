from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox


def open_image(path, parent=None):
    path = Path(path)
    if not path.is_file():
        QMessageBox.warning(parent, "无法打开图片", f"图片不存在：\n{path}")
        return False
    if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
        QMessageBox.warning(parent, "无法打开图片", f"系统无法打开此图片：\n{path}")
        return False
    return True
