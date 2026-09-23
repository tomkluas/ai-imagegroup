import json
import sqlite3
import zipfile
from pathlib import Path

import numpy as np
import pytest

from image_group.application import ClassificationController
from image_group.backup.service import BackupError, BackupService
from image_group.output.service import OutputService
from image_group.people.service import PeopleService
from image_group.storage.database import Database
from image_group.storage.repositories import PersonRepository
from image_group.tasks.runner import TaskItem, TaskRunner


def malicious_archive(path: Path, name: str):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(name, b"owned")
        import hashlib
        archive.writestr("manifest.json", json.dumps({"version": 1, "files": {name: hashlib.sha256(b"owned").hexdigest()}}))


@pytest.mark.parametrize("name", ["..\\outside.txt", "C:/outside.txt", "//server/share.txt"])
def test_restore_rejects_windows_escape_paths(tmp_path, name):
    archive = tmp_path / "bad.zip"; malicious_archive(archive, name)
    with pytest.raises(BackupError): BackupService(tmp_path / "data").restore(archive)
    assert not (tmp_path / "outside.txt").exists()


def test_failed_restore_keeps_existing_library(tmp_path, monkeypatch):
    data = tmp_path / "data"; data.mkdir(); (data / "sentinel.txt").write_text("original")
    source = tmp_path / "source"; source.mkdir(); (source / "new.txt").write_text("new")
    archive = BackupService(source).create(tmp_path / "backup.zip")
    original_replace = Path.replace
    def fail_new_swap(self, target):
        if self.name.startswith("restore-"):
            raise OSError("swap failed")
        return original_replace(self, target)
    monkeypatch.setattr(Path, "replace", fail_new_swap)
    with pytest.raises(OSError): BackupService(data).restore(archive)
    assert (data / "sentinel.txt").read_text() == "original"


def test_hash_suffix_collision_never_returns_wrong_content(tmp_path):
    source = tmp_path / "a" / "IMG.jpg"; source.parent.mkdir(); source.write_bytes(b"second")
    service = OutputService(tmp_path / "out", {"p1": "张小明"}); folder = service.person_dir("t", "p1"); folder.mkdir(parents=True)
    digest = service._sha(source); (folder / f"IMG_{digest[:8]}.jpg").write_bytes(b"wrong")
    target = service.materialize("t", source, ["p1"])[0]
    assert target.read_bytes() == b"second" and target.name != f"IMG_{digest[:8]}.jpg"


class Validator:
    def validate(self, path): return type("R", (), {"content_sha256":"h", "feature":b"f", "model_version":"m"})()


def test_delete_person_used_by_task_removes_managed_data_not_source(tmp_path):
    db = Database(tmp_path / "data.db"); db.migrate(); service = PeopleService(db, PersonRepository(db), tmp_path / "refs", Validator())
    person = service.create_person("张小明"); source = tmp_path / "source.jpg"; source.write_bytes(b"x"); ref = service.import_reference(person.id, source)
    db.execute("INSERT INTO tasks(id,name,input_kind,output_root,status,created_at,updated_at) VALUES('t','n','files','o','done','x','x')")
    db.execute("INSERT INTO task_people(task_id,person_id) VALUES('t',?)", (person.id,))
    service.delete_person(person.id)
    assert source.exists() and not ref.managed_path.exists() and db.scalar("SELECT count(*) FROM people") == 0


class Processor:
    def __init__(self): self.calls = []
    def recognize(self, path): self.calls.append(path.name); return ["p"]
class FlakyOutput:
    def __init__(self): self.fail = True
    def materialize(self, task_id, source, people):
        if self.fail: self.fail = False; raise OSError(28, "full")
        return [Path("ok")]


def test_runner_resumes_unrecognized_later_photos(tmp_path):
    items=[]
    for name in ("a.jpg","b.jpg"):
        path=tmp_path/name;path.write_bytes(b"x");items.append(TaskItem(name,path))
    processor=Processor();runner=TaskRunner(processor,FlakyOutput());runner.create("t",items);runner.start("t");runner.resume("t")
    assert runner.state("t") == "completed" and processor.calls == ["a.jpg", "b.jpg"]


class BadThenGoodLoader:
    def __init__(self): self.calls=0
    def analysis_image(self,path,max_long_edge):
        self.calls+=1
        if self.calls==1: raise ValueError("corrupt")
        return type("L",(),{"image":np.zeros((2,2,3),np.uint8)})()
class EmptyBackend:
    def detect_and_embed(self,image): return []


def test_corrupt_photo_is_recorded_and_next_photo_continues(tmp_path):
    db=Database(tmp_path/"data.db");db.migrate();person=PersonRepository(db).create("张小明")
    files=[]
    for name in ("bad.jpg","good.jpg"):
        path=tmp_path/name;path.write_bytes(name.encode());files.append(path)
    task=ClassificationController(db,EmptyBackend(),BadThenGoodLoader()).start("n",files,tmp_path/"out",[person.id])
    rows=db.execute("SELECT status,error FROM task_photos WHERE task_id=? ORDER BY source_path",(task,)).fetchall()
    assert [r[0] for r in rows] == ["error", "recognized"] and rows[0][1]
