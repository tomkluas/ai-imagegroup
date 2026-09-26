from pathlib import Path


def test_spec_removes_foreign_icu_dlls_from_bundle():
    spec = (Path(__file__).parents[2] / "packaging" / "ImageGroup.spec").read_text(
        encoding="utf-8"
    )

    assert '"icuuc.dll"' in spec
    assert '"icudt78.dll"' in spec
    assert "a.binaries =" in spec
