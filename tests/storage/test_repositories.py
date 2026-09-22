from __future__ import annotations

import pytest

from image_group.storage.database import Database
from image_group.storage.repositories import DuplicateNameError, PersonRepository


def make_person_repo(tmp_path):
    db = Database(tmp_path / "data.db")
    db.migrate()
    return PersonRepository(db)


def test_person_round_trip(tmp_path):
    repo = make_person_repo(tmp_path)

    person = repo.create("张小明")

    assert repo.get(person.id) == person
    assert repo.list_all() == [person]


def test_duplicate_display_name_is_rejected(tmp_path):
    repo = make_person_repo(tmp_path)
    repo.create("张小明")

    with pytest.raises(DuplicateNameError):
        repo.create("张小明")


def test_person_ids_are_uuid_strings(tmp_path):
    repo = make_person_repo(tmp_path)

    person = repo.create("李小红")

    assert len(person.id) == 36
    assert person.id.count("-") == 4
