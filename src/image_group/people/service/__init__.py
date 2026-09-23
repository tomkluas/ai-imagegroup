from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from image_group.domain.models import Person, ReferencePhoto
from image_group.storage.database import Database
from image_group.storage.repositories import (
    DuplicateNameError,
    PersonNotFoundError,
    PersonRepository,
    utc_now,
)

RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
INVALID = set('<>:"/\\|?*')
SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class InvalidPersonNameError(ValueError): pass
class ReferenceValidator(Protocol):
    def validate(self, path: Path): ...


@dataclass(frozen=True, slots=True)
class ImportFailure:
    path: Path
    reason: str


@dataclass(frozen=True, slots=True)
class BulkImportResult:
    created_people: list[str]
    imported_count: int
    failures: list[ImportFailure]
    warnings: list[str]


def validate_person_name(name: str) -> str:
    clean = name.strip()
    if not clean or clean.endswith((".", " ")) or any(c in INVALID for c in clean) or clean.upper().split(".", 1)[0] in RESERVED:
        raise InvalidPersonNameError(name)
    return clean


class PeopleService:
    def __init__(self, database: Database, people: PersonRepository, reference_root: Path, validator: ReferenceValidator):
        self.database, self.people, self.validator = database, people, validator
        self.reference_root = Path(reference_root).resolve()
        self.reference_root.mkdir(parents=True, exist_ok=True)

    def create_person(self, name: str) -> Person:
        return self.people.create(validate_person_name(name))

    def rename_person(self, person_id: str, name: str) -> Person:
        clean = validate_person_name(name)
        try:
            cursor = self.database.execute("UPDATE people SET display_name=?, updated_at=? WHERE id=?", (clean, utc_now(), person_id))
        except Exception as exc:
            if "UNIQUE" in str(exc).upper(): raise DuplicateNameError(clean) from exc
            raise
        if cursor.rowcount == 0: raise PersonNotFoundError(person_id)
        return self.people.get(person_id)

    def import_reference(self, person_id: str, source: Path) -> ReferencePhoto:
        source = Path(source).resolve(strict=True)
        self.people.get(person_id)
        valid = self.validator.validate(source)
        rid = str(uuid4())
        managed = self.reference_root / f"{rid}{source.suffix.lower()}"
        part = managed.with_suffix(managed.suffix + ".part")
        shutil.copyfile(source, part)
        with part.open("r+b") as handle: os.fsync(handle.fileno())
        part.replace(managed)
        ref = ReferencePhoto(rid, person_id, source, managed, valid.content_sha256, "valid", utc_now())
        try:
            self.database.execute("INSERT INTO reference_photos(id,person_id,source_path,managed_path,content_sha256,status,feature,model_version,created_at) VALUES(?,?,?,?,?,?,?,?,?)", (ref.id, ref.person_id, str(ref.source_path), str(ref.managed_path), ref.content_sha256, ref.status, valid.feature, valid.model_version, ref.created_at))
        except BaseException:
            managed.unlink(missing_ok=True)
            raise
        return ref

    def delete_reference(self, reference_id: str) -> None:
        row = self.database.execute("SELECT managed_path FROM reference_photos WHERE id=?", (reference_id,)).fetchone()
        if row is None: return
        path = Path(row[0]).resolve()
        self._require_managed(path)
        with self.database.transaction(): self.database.execute("DELETE FROM reference_photos WHERE id=?", (reference_id,))
        path.unlink(missing_ok=True)

    def delete_person(self, person_id: str) -> None:
        paths = [Path(r[0]).resolve() for r in self.database.execute("SELECT managed_path FROM reference_photos WHERE person_id=?", (person_id,)).fetchall()]
        for path in paths: self._require_managed(path)
        with self.database.transaction():
            self.database.execute("DELETE FROM assignments WHERE person_id=?", (person_id,))
            self.database.execute("DELETE FROM task_people WHERE person_id=?", (person_id,))
            cursor = self.database.execute("DELETE FROM people WHERE id=?", (person_id,))
            if cursor.rowcount == 0: raise PersonNotFoundError(person_id)
        for path in paths: path.unlink(missing_ok=True)

    def bulk_import(self, root: Path) -> BulkImportResult:
        created, failures, warnings, count = [], [], [], 0
        for folder in sorted((p for p in Path(root).iterdir() if p.is_dir()), key=lambda p: p.name):
            try:
                person = self.create_person(folder.name); created.append(person.display_name)
            except Exception as exc:
                failures.append(ImportFailure(folder, str(exc))); continue
            child_count = 0
            for source in sorted(folder.iterdir()):
                if not source.is_file() or source.suffix.lower() not in SUFFIXES: continue
                try:
                    self.import_reference(person.id, source); count += 1; child_count += 1
                except Exception as exc: failures.append(ImportFailure(source, str(exc)))
            if child_count < 3: warnings.append(f"{person.display_name} 的有效参考照片少于 3 张")
        return BulkImportResult(created, count, failures, warnings)

    def _require_managed(self, path: Path) -> None:
        if not path.is_relative_to(self.reference_root): raise RuntimeError("参考照片路径超出应用目录")
