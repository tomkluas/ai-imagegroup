from image_group.output.service import OutputService

def test_group_photo_is_copied_once_per_distinct_person(tmp_path):
    source = tmp_path / "source" / "活动.jpg"; source.parent.mkdir(); source.write_bytes(b"photo")
    output = OutputService(tmp_path / "result", {"p1": "张小明", "p2": "李小红"})
    paths = output.materialize("t1", source, ["p1", "p2", "p1"])
    assert len(paths) == 2 and all(path.read_bytes() == b"photo" for path in paths)
    assert source.exists()

def test_same_filename_different_content_never_overwrites(tmp_path):
    first = tmp_path / "a" / "IMG.jpg"; second = tmp_path / "b" / "IMG.jpg"
    first.parent.mkdir(); second.parent.mkdir(); first.write_bytes(b"first"); second.write_bytes(b"second")
    output = OutputService(tmp_path / "result", {"p1": "张小明"})
    a = output.materialize("t1", first, ["p1"])[0]
    b = output.materialize("t1", second, ["p1"])[0]
    assert a != b and {a.read_bytes(), b.read_bytes()} == {b"first", b"second"}

def test_repeating_same_source_reuses_existing_copy(tmp_path):
    source = tmp_path / "IMG.jpg"; source.write_bytes(b"same")
    output = OutputService(tmp_path / "result", {"p1": "张小明"})
    assert output.materialize("t1", source, ["p1"])[0] == output.materialize("t1", source, ["p1"])[0]
