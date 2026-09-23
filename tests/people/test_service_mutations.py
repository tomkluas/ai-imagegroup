from dataclasses import dataclass
from pathlib import Path

from image_group.people.service import PeopleService
from image_group.storage.database import Database
from image_group.storage.repositories import PersonRepository


@dataclass(frozen=True)
class Valid:
    content_sha256: str = "hash"
    feature: bytes = b"feature"
    model_version: str = "test"

class Validator:
    def validate(self, path: Path): return Valid()

def make_service(tmp_path):
    db = Database(tmp_path / "data.db"); db.migrate()
    return PeopleService(db, PersonRepository(db), tmp_path / "refs", Validator())

def test_rename_person_updates_display_name(tmp_path):
    service = make_service(tmp_path); person = service.create_person("旧名字")
    assert service.rename_person(person.id, "新名字").display_name == "新名字"

def test_delete_reference_removes_managed_copy_only(tmp_path):
    service = make_service(tmp_path); person = service.create_person("张小明")
    source = tmp_path / "source.jpg"; source.write_bytes(b"image")
    ref = service.import_reference(person.id, source)
    service.delete_reference(ref.id)
    assert source.exists() and not ref.managed_path.exists()
