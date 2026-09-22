from dataclasses import dataclass
from pathlib import Path
import pytest
from image_group.people.service import InvalidPersonNameError, PeopleService
from image_group.storage.database import Database
from image_group.storage.repositories import PersonRepository

@dataclass(frozen=True)
class AcceptedReference:
    content_sha256: str = "abc123"
    feature: bytes = b"feature"
    model_version: str = "test-v1"

class AcceptingValidator:
    def validate(self, path: Path) -> AcceptedReference:
        return AcceptedReference()

@pytest.fixture
def service(tmp_path):
    db = Database(tmp_path / "app" / "data.db"); db.migrate()
    return PeopleService(db, PersonRepository(db), tmp_path / "app" / "reference", AcceptingValidator())

def test_import_copies_source_and_delete_never_removes_source(service, tmp_path):
    source = tmp_path / "源照片.jpg"; source.write_bytes(b"jpeg")
    person = service.create_person("张小明")
    ref = service.import_reference(person.id, source)
    assert ref.managed_path.read_bytes() == b"jpeg"
    service.delete_person(person.id)
    assert source.exists() and not ref.managed_path.exists()

@pytest.mark.parametrize("name", ["", "CON", "张/小明", "张小明."])
def test_invalid_windows_names_are_rejected(service, name):
    with pytest.raises(InvalidPersonNameError): service.create_person(name)

def test_bulk_import_uses_child_directory_as_name(service, tmp_path):
    root = tmp_path / "参考照片"
    for name in ("张小明", "李小红"):
        folder = root / name; folder.mkdir(parents=True)
        for index in range(3): (folder / f"{index}.jpg").write_bytes(f"{name}-{index}".encode())
    result = service.bulk_import(root)
    assert result.created_people == ["张小明", "李小红"]
    assert result.imported_count == 6 and result.failures == []

def test_bulk_import_reports_validator_failure(tmp_path):
    class RejectingValidator:
        def validate(self, path): raise ValueError("未检测到人脸")
    db = Database(tmp_path / "app" / "data.db"); db.migrate()
    service = PeopleService(db, PersonRepository(db), tmp_path / "app" / "reference", RejectingValidator())
    folder = tmp_path / "参考照片" / "张小明"; folder.mkdir(parents=True)
    (folder / "1.jpg").write_bytes(b"bad")
    result = service.bulk_import(tmp_path / "参考照片")
    assert result.imported_count == 0 and result.failures[0].reason == "未检测到人脸"

