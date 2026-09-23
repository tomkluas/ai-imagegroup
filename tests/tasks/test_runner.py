from pathlib import Path
from image_group.tasks.runner import TaskItem, TaskRunner
class Processor:
    def __init__(self): self.calls = 0
    def recognize(self, path): self.calls += 1; return ["p1"]
class Output:
    def __init__(self): self.full = True; self.calls = 0
    def materialize(self, task_id, source, people):
        self.calls += 1
        if self.full: raise OSError(28, "disk full")
        return [Path("done")]
def test_disk_full_preserves_recognition_and_resume_only_retries_copy(tmp_path):
    photo = tmp_path / "a.jpg"; photo.write_bytes(b"a")
    processor, output = Processor(), Output(); runner = TaskRunner(processor, output)
    runner.create("t1", [TaskItem("x", photo)])
    runner.start("t1")
    assert runner.state("t1") == "copy_paused" and runner.recognized_count("t1") == 1
    output.full = False; runner.resume("t1")
    assert runner.state("t1") == "completed" and processor.calls == 1
def test_cancel_stops_before_next_item(tmp_path):
    files = []
    for name in ("a.jpg", "b.jpg"):
        path = tmp_path / name; path.write_bytes(b"x"); files.append(TaskItem(name, path))
    processor, output = Processor(), Output(); output.full = False
    runner = TaskRunner(processor, output); runner.create("t1", files); runner.cancel("t1"); runner.start("t1")
    assert runner.state("t1") == "cancelled" and processor.calls == 0
