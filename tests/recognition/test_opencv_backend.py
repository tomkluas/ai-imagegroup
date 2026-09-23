from pathlib import Path

import cv2
import numpy as np
import pytest

from image_group.recognition.opencv_backend import (
    ModelIntegrityError,
    OpenCvRecognitionBackend,
    ReferenceValidationError,
)

ROOT = Path(__file__).parents[2]; MODELS = ROOT / "resources" / "models"; LENA = ROOT / "tests" / "fixtures" / "lena.jpg"
@pytest.fixture(scope="module")
def backend(): return OpenCvRecognitionBackend(MODELS)
def test_model_hash_mismatch_is_rejected(tmp_path):
    (tmp_path / "face_detection_yunet_2023mar.onnx").write_bytes(b"bad")
    (tmp_path / "face_recognition_sface_2021dec.onnx").write_bytes(b"bad")
    with pytest.raises(ModelIntegrityError): OpenCvRecognitionBackend(tmp_path)
def test_reference_returns_normalized_feature(backend):
    result = backend.validate_reference(LENA)
    assert result.feature.ndim == 1 and result.feature.size > 0
    assert np.isclose(np.linalg.norm(result.feature), 1.0, atol=1e-4)
def test_reference_rejects_zero_or_multiple_faces(backend, tmp_path):
    blank = tmp_path / "blank.jpg"; cv2.imwrite(str(blank), np.zeros((512, 512, 3), np.uint8))
    with pytest.raises(ReferenceValidationError, match="未检测到"): backend.validate_reference(blank)
    face = cv2.imread(str(LENA)); group = np.concatenate([face, face], axis=1)
    group_path = tmp_path / "group.jpg"; cv2.imwrite(str(group_path), group)
    with pytest.raises(ReferenceValidationError, match="多张"): backend.validate_reference(group_path)
