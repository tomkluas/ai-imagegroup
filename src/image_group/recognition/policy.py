from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from image_group.domain.models import FaceDecision
from image_group.recognition.base import DetectedFace


@dataclass(frozen=True, slots=True)
class PolicyConfig:
    auto_score: float = 0.50
    review_score: float = 0.36
    auto_margin: float = 0.08
    min_face_size: int = 40
@dataclass(frozen=True, slots=True)
class Candidate:
    person_id: str
    score: float
@dataclass(frozen=True, slots=True)
class FaceMatch:
    candidates: tuple[Candidate, ...]
    decision: FaceDecision
    reason: str

class DecisionPolicy:
    def __init__(self, config: PolicyConfig | None = None): self.config = config or PolicyConfig()
    def classify(self, face: DetectedFace, gallery: dict[str, list[np.ndarray]]) -> FaceMatch:
        if face.face_size < self.config.min_face_size: return FaceMatch((), FaceDecision.UNKNOWN, "face_too_small")
        if not np.all(np.isfinite(face.embedding)): return FaceMatch((), FaceDecision.UNKNOWN, "invalid_embedding")
        candidates = []
        for person_id, references in gallery.items():
            scores = [float(np.dot(face.embedding, ref)) for ref in references if ref.shape == face.embedding.shape and np.all(np.isfinite(ref))]
            if scores: candidates.append(Candidate(person_id, max(scores)))
        candidates.sort(key=lambda item: (-item.score, item.person_id)); top = tuple(candidates[:3])
        if not top or top[0].score < self.config.review_score: return FaceMatch(top, FaceDecision.UNKNOWN, "low_score")
        if top[0].score < self.config.auto_score: return FaceMatch(top, FaceDecision.REVIEW, "review_score")
        if len(top) > 1 and top[0].score - top[1].score < self.config.auto_margin: return FaceMatch(top, FaceDecision.REVIEW, "ambiguous_margin")
        return FaceMatch(top, FaceDecision.AUTO, "high_confidence")
