from pathlib import Path

from image_group.app import build_main_window


def test_build_main_window_creates_local_database(qtbot, tmp_path):
    models = Path(__file__).parents[2] / "resources" / "models"
    window = build_main_window(tmp_path / "appdata", models); qtbot.addWidget(window)
    assert (tmp_path / "appdata" / "data.db").exists()
    assert window.windowTitle() == "园区照片分类助手"
