from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
import numpy as np

from image_group.photos.io import ImageLoader
from image_group.recognition.base import DetectedFace, ValidatedReference

HASHES = {
 "face_detection_yunet_2023mar.onnx": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
 "face_recognition_sface_2021dec.onnx": "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
}
class ModelIntegrityError(RuntimeError): pass
class ReferenceValidationError(ValueError): pass
class OpenCvRecognitionBackend:
    model_version = "opencv-zoo-yunet2023mar-sface2021dec"
    def __init__(self, model_root: Path):
        root = Path(model_root)
        for name, expected in HASHES.items():
            path = root / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected: raise ModelIntegrityError(name)
        self.detector = cv2.FaceDetectorYN.create(str(root / "face_detection_yunet_2023mar.onnx"), "", (320, 320), 0.6, 0.3, 5000)
        self.recognizer = cv2.FaceRecognizerSF.create(str(root / "face_recognition_sface_2021dec.onnx"), "")
    def validate_reference(self, path: Path) -> ValidatedReference:
        loaded = ImageLoader().analysis_image(path, 1280); faces = self.detect_and_embed(loaded.image)
        if not faces: raise ReferenceValidationError("未检测到人脸")
        if len(faces) != 1: raise ReferenceValidationError("检测到多张人脸")
        if faces[0].face_size < 80: raise ReferenceValidationError("人脸尺寸过小")
        return ValidatedReference(hashlib.sha256(Path(path).read_bytes()).hexdigest(), faces[0].embedding, self.model_version)
    def detect_and_embed(self, image: np.ndarray) -> list[DetectedFace]:
        h, w = image.shape[:2]; self.detector.setInputSize((w, h)); _, rows = self.detector.detect(image)
        if rows is None: return []
        result = []
        for row in rows:
            aligned = self.recognizer.alignCrop(image, row); feature = self.recognizer.feature(aligned).reshape(-1).astype(np.float32)
            norm = float(np.linalg.norm(feature))
            if not np.isfinite(norm) or norm == 0: continue
            x, y, bw, bh = (int(round(v)) for v in row[:4])
            result.append(DetectedFace((x, y, bw, bh), tuple(float(v) for v in row[4:14]), float(row[14]), min(bw, bh), feature / norm))
        return result

