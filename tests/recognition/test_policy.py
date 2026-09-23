import numpy as np
from image_group.domain.models import FaceDecision
from image_group.recognition.base import DetectedFace
from image_group.recognition.policy import DecisionPolicy, PolicyConfig

def vector(x, y):
    value = np.array([x, y], np.float32); return value / np.linalg.norm(value)
def face(embedding, size=100, score=0.9):
    return DetectedFace((0, 0, size, size), (), score, size, embedding)

def test_high_score_with_clear_margin_is_auto():
    match = DecisionPolicy().classify(face(vector(1, 0)), {"p1": [vector(1, 0)], "p2": [vector(0, 1)]})
    assert match.decision is FaceDecision.AUTO and match.candidates[0].person_id == "p1"
def test_close_first_and_second_candidates_require_review():
    policy = DecisionPolicy(PolicyConfig(auto_score=.5, review_score=.36, auto_margin=.08, min_face_size=40))
    match = policy.classify(face(vector(1, 0)), {"p1": [vector(.62, .78)], "p2": [vector(.60, .80)]})
    assert match.decision is FaceDecision.REVIEW and match.reason == "ambiguous_margin"
def test_low_quality_or_low_score_is_unknown():
    match = DecisionPolicy().classify(face(vector(1, 0), size=20), {"p1": [vector(1, 0)]})
    assert match.decision is FaceDecision.UNKNOWN and match.reason == "face_too_small"
def test_empty_gallery_and_nan_are_unknown():
    policy = DecisionPolicy()
    assert policy.classify(face(vector(1, 0)), {}).decision is FaceDecision.UNKNOWN
    assert policy.classify(face(np.array([np.nan, 0], np.float32)), {"p1": [vector(1, 0)]}).decision is FaceDecision.UNKNOWN
def test_multiple_references_produce_one_candidate():
    match = DecisionPolicy().classify(face(vector(1, 0)), {"p1": [vector(0, 1), vector(1, 0)]})
    assert len(match.candidates) == 1 and match.candidates[0].score == 1.0
