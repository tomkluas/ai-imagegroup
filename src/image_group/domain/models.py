from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class FaceDecision(StrEnum):
    AUTO = "auto"
    REVIEW = "review"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Person:
    id: str
    display_name: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ReferencePhoto:
    id: str
    person_id: str
    source_path: Path
    managed_path: Path
    content_sha256: str
    status: str
    created_at: str


@dataclass(frozen=True, slots=True)
class ClassificationTask:
    id: str
    name: str
    input_kind: str
    output_root: Path
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class TaskPhoto:
    id: str
    task_id: str
    source_path: Path
    content_sha256: str
    status: str
    error: str | None

