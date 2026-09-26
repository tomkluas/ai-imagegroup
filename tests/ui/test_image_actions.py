from pathlib import Path

from image_group.ui import image_actions


def test_open_image_uses_system_default_application(monkeypatch, tmp_path):
    path = tmp_path / "photo.jpg"
    path.write_bytes(b"photo")
    opened = []
    monkeypatch.setattr(
        image_actions.QDesktopServices,
        "openUrl",
        lambda url: opened.append(url.toLocalFile()) or True,
    )
    assert image_actions.open_image(path) is True
    assert [Path(value) for value in opened] == [path]


def test_open_image_does_not_launch_missing_file(monkeypatch, tmp_path):
    warnings = []
    monkeypatch.setattr(
        image_actions.QMessageBox,
        "warning",
        lambda _parent, title, message: warnings.append((title, message)),
    )
    monkeypatch.setattr(
        image_actions.QDesktopServices,
        "openUrl",
        lambda _url: (_ for _ in ()).throw(AssertionError("must not open")),
    )
    assert image_actions.open_image(tmp_path / "missing.jpg") is False
    assert warnings and "不存在" in warnings[0][1]
