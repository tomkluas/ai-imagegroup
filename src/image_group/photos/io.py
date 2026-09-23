from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


class ImageDecodeError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class LoadedImage:
    image: np.ndarray
    original_size: tuple[int, int]
    analysis_size: tuple[int, int]
    scale: float
    orientation_applied: bool


class ImageLoader:
    def analysis_image(self, path: Path, max_long_edge: int) -> LoadedImage:
        path = Path(path)
        try:
            with Image.open(path) as source:
                source.load()
                original_size = source.size
                orientation = source.getexif().get(274, 1)
                oriented = ImageOps.exif_transpose(source).convert("RGB")
        except (OSError, UnidentifiedImageError) as exc:
            raise ImageDecodeError(f"无法读取图片: {path}") from exc
        width, height = oriented.size
        scale = min(1.0, max_long_edge / max(width, height))
        if scale < 1.0:
            oriented = oriented.resize(
                (max(1, round(width * scale)), max(1, round(height * scale))),
                Image.Resampling.LANCZOS,
            )
        rgb = np.asarray(oriented)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        return LoadedImage(
            image=bgr,
            original_size=original_size,
            analysis_size=oriented.size,
            scale=scale,
            orientation_applied=orientation != 1,
        )
