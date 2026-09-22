from __future__ import annotations

import pytest

from image_group.storage.database import Database


def test_new_database_has_schema_and_foreign_keys(tmp_path):
    db = Database(tmp_path / "data.db")
    db.migrate()

    assert db.scalar("PRAGMA user_version") == 1
    assert db.scalar("PRAGMA foreign_keys") == 1
    assert {
        "people",
        "reference_photos",
        "tasks",
        "task_photos",
        "faces",
        "assignments",
    } <= db.table_names()


def test_transaction_rolls_back_all_writes(tmp_path):
    db = Database(tmp_path / "data.db")
    db.migrate()

    with pytest.raises(RuntimeError, match="stop"), db.transaction():
        db.execute(
            "INSERT INTO people(id, display_name, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            ("p1", "甲", "2026-09-22T00:00:00+00:00", "2026-09-22T00:00:00+00:00"),
        )
        raise RuntimeError("stop")

    assert db.scalar("SELECT count(*) FROM people") == 0

