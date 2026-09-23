from __future__ import annotations
import hashlib
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
@dataclass(frozen=True, slots=True)
class ScannedPhoto: path: Path; sha256: str; size: int
@dataclass(frozen=True, slots=True)
class ScanError: path: Path; reason: str
@dataclass(frozen=True, slots=True)
class ScanResult:
    photos: list[ScannedPhoto]; duplicates: list[Path]; errors: list[ScanError]

def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""): digest.update(block)
    return digest.hexdigest()

class PhotoScanner:
    def scan(self, paths: list[Path]) -> ScanResult:
        candidates: list[Path] = []
        for raw in paths:
            path = Path(raw)
            if path.is_dir(): candidates.extend(sorted(p for p in path.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES))
            else: candidates.append(path)
        photos, duplicates, errors, seen = [], [], [], set()
        for path in candidates:
            if not path.is_file(): errors.append(ScanError(path, "文件不存在")); continue
            if path.suffix.lower() not in SUPPORTED_SUFFIXES: continue
            try: digest = file_sha256(path)
            except OSError as exc: errors.append(ScanError(path, str(exc))); continue
            if digest in seen: duplicates.append(path); continue
            seen.add(digest); photos.append(ScannedPhoto(path.resolve(), digest, path.stat().st_size))
        return ScanResult(photos, duplicates, errors)

