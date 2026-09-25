from pathlib import Path


def test_release_is_a_single_file_executable():
    spec = (Path(__file__).parents[2] / "packaging" / "ImageGroup.spec").read_text(
        encoding="utf-8"
    )

    assert "exclude_binaries=False" in spec
    assert "COLLECT(" not in spec
