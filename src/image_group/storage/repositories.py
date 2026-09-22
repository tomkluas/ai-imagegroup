from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from image_group.domain.models import ClassificationTask, Person
from image_group.storage.database import Database


class DuplicateNameError(ValueError):
    pass


class PersonNotFoundError(LookupError):
    pass


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class PersonRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, display_name: str) -> Person:
        person = Person(str(uuid4()), display_name, utc_now(), utc_now())
        try:
            self.database.execute(
                "INSERT INTO people(id, display_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (person.id, person.display_name, person.created_at, person.updated_at),
            )
        except sqlite3.IntegrityError as exc:
            raise DuplicateNameError(display_name) from exc
        return person

    def get(self, person_id: str) -> Person:
        row = self.database.execute(
            "SELECT id, display_name, created_at, updated_at FROM people WHERE id = ?",
            (person_id,),
        ).fetchone()
        if row is None:
            raise PersonNotFoundError(person_id)
        return Person(**dict(row))

    def list_all(self) -> list[Person]:
        rows = self.database.execute(
            "SELECT id, display_name, created_at, updated_at FROM people "
            "ORDER BY display_name COLLATE NOCASE, id"
        ).fetchall()
        return [Person(**dict(row)) for row in rows]


class TaskRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, name: str, input_kind: str, output_root: Path) -> ClassificationTask:
        now = utc_now()
        task = ClassificationTask(
            id=str(uuid4()),
            name=name,
            input_kind=input_kind,
            output_root=Path(output_root),
            status="created",
            created_at=now,
            updated_at=now,
        )
        self.database.execute(
            "INSERT INTO tasks(id, name, input_kind, output_root, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                task.id,
                task.name,
                task.input_kind,
                str(task.output_root),
                task.status,
                task.created_at,
                task.updated_at,
            ),
        )
        return task
