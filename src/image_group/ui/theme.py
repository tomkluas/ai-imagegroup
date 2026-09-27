"""Shared visual theme for the desktop application."""

APP_STYLESHEET = """
QMainWindow#mainWindow, QWidget#appCanvas {
    background: #f3f6f4;
}
QWidget {
    color: #26352e;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
    font-size: 10pt;
}
QLabel#pageTitle {
    color: #203d30;
    font-size: 21pt;
    font-weight: 700;
    padding: 2px 0 6px 0;
}
QLabel#sectionTitle {
    color: #30483c;
    font-size: 12pt;
    font-weight: 650;
}
QLabel#mutedText {
    color: #78867e;
}
QListWidget {
    background: #ffffff;
    border: 1px solid #e0e8e2;
    border-radius: 10px;
    padding: 7px;
    outline: none;
    selection-background-color: #e7f3eb;
    selection-color: #174e32;
}
QListWidget::item {
    border-radius: 6px;
    padding: 8px;
}
QListWidget::item:hover {
    background: #f2f7f3;
}
QListWidget::item:selected {
    background: #e6f2e9;
    color: #174e32;
}
QListWidget#navigationList {
    background: #ffffff;
    border: 1px solid #e2e9e3;
    border-radius: 12px;
    padding: 9px 7px;
}
QListWidget#navigationList::item {
    min-height: 34px;
    margin: 2px 1px;
    padding: 5px 10px;
    color: #53635a;
}
QListWidget#navigationList::item:hover {
    background: #f2f7f3;
    color: #244b35;
}
QListWidget#navigationList::item:selected {
    background: #e8f3eb;
    color: #17643a;
    font-weight: 650;
    border-left: 3px solid #27834b;
}
QLineEdit, QComboBox {
    min-height: 34px;
    background: #ffffff;
    border: 1px solid #d7e0d9;
    border-radius: 7px;
    padding: 3px 10px;
    selection-background-color: #318451;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #378957;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QPushButton {
    min-height: 36px;
    background: #ffffff;
    border: 1px solid #d8e2da;
    border-radius: 7px;
    padding: 4px 14px;
    color: #34483c;
}
QPushButton:hover {
    background: #f1f7f2;
    border-color: #9dbda7;
}
QPushButton:pressed {
    background: #e4eee6;
}
QPushButton:disabled {
    color: #9aa69e;
    background: #edf0ee;
    border-color: #e2e6e3;
}
QPushButton[primaryAction="true"] {
    color: #ffffff;
    background: #267a45;
    border: 1px solid #267a45;
    font-weight: 650;
}
QPushButton[primaryAction="true"]:hover {
    background: #1f693b;
    border-color: #1f693b;
}
QPushButton[primaryAction="true"]:pressed {
    background: #185a32;
}
QPushButton[dangerAction="true"] {
    color: #9b3d38;
}
QPushButton[dangerAction="true"]:hover {
    background: #fff3f1;
    border-color: #e2aaa4;
}
QGroupBox {
    color: #30483c;
}
QProgressBar {
    min-height: 13px;
    max-height: 13px;
    background: #e8eee9;
    border: none;
    border-radius: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background: #318451;
    border-radius: 6px;
}
QScrollBar:vertical {
    background: transparent;
    width: 11px;
    margin: 3px;
}
QScrollBar::handle:vertical {
    background: #cbd7ce;
    min-height: 28px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #aebeb2;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
    height: 0;
}
"""
