from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import numpy as np
@dataclass(frozen=True, slots=True)
class DetectedFace:
    box: tuple[int, int, int, int]
    landmarks: tuple[float, ...]
    detection_score: float
    face_size: int
    embedding: np.ndarray
@dataclass(frozen=True, slots=True)
class ValidatedReference:
    content_sha256: str
    feature: np.ndarray
    model_version: str
class RecognitionBackend(Protocol):
    def validate_reference(self, path: Path) -> ValidatedReference: ...
    def detect_and_embed(self, image: np.ndarray) -> list[DetectedFace]: ...

