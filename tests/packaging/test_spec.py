from pathlib import Path


def test_spec_collects_required_pyside_runtime_dlls():
    spec = (Path(__file__).parents[2] / "packaging" / "ImageGroup.spec").read_text(
        encoding="utf-8"
    )

    assert 'pyside_root / "concrt140.dll"' in spec
    assert 'pyside_root / "msvcp140_codecvt_ids.dll"' in spec
    assert "binaries=pyside_binaries" in spec
