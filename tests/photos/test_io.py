from pathlib import Path

import pytest
from PIL import Image

from image_group.photos.io import ImageDecodeError, ImageLoader


def make_jpeg(path: Path, size=(1600, 1200), orientation=None):
    image = Image.new("RGB", size, (10, 20, 30))
    exif = Image.Exif()
    if orientation: exif[274] = orientation
    image.save(path, exif=exif)

def test_analysis_image_bounds_long_edge(tmp_path):
    path = tmp_path / "中文照片.jpg"; make_jpeg(path)
    loaded = ImageLoader().analysis_image(path, 800)
    assert loaded.image.shape[:2] == (600, 800)
    assert loaded.original_size == (1600, 1200)

def test_analysis_image_applies_exif_orientation(tmp_path):
    path = tmp_path / "rotated.jpg"; make_jpeg(path, (1600, 1200), 6)
    loaded = ImageLoader().analysis_image(path, 800)
    assert loaded.image.shape[:2] == (800, 600)
    assert loaded.orientation_applied is True

def test_corrupt_image_has_path_in_error(tmp_path):
    path = tmp_path / "坏图.jpg"; path.write_bytes(b"not-image")
    with pytest.raises(ImageDecodeError, match="坏图.jpg"):
        ImageLoader().analysis_image(path, 800)
