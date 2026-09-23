from pathlib import Path
from image_group.tasks.scanner import PhotoScanner

def test_same_content_selected_by_two_paths_is_scanned_once(tmp_path):
    first = tmp_path / "a.jpg"; second = tmp_path / "b.jpg"
    first.write_bytes(b"same-photo"); second.write_bytes(b"same-photo")
    result = PhotoScanner().scan([first, second])
    assert len(result.photos) == 1 and len(result.duplicates) == 1

def test_folder_scan_is_not_recursive_and_filters_extensions(tmp_path):
    (tmp_path / "one.JPG").write_bytes(b"one")
    (tmp_path / "note.txt").write_text("x")
    nested = tmp_path / "old-output"; nested.mkdir(); (nested / "two.jpg").write_bytes(b"two")
    result = PhotoScanner().scan([tmp_path])
    assert [item.path.name for item in result.photos] == ["one.JPG"]

def test_missing_file_is_reported_without_stopping(tmp_path):
    good = tmp_path / "ok.png"; good.write_bytes(b"ok")
    result = PhotoScanner().scan([tmp_path / "missing.jpg", good])
    assert len(result.photos) == 1 and result.errors[0].path.name == "missing.jpg"

