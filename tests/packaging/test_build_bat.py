from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "一键重新打包.bat"


def _write_fake_uv(directory: Path, *, fail_on: str | None = None) -> None:
    failure = f'echo %* | findstr /C:"{fail_on}" >nul && exit /b 7' if fail_on else ""
    (directory / "uv.cmd").write_text(
        "@echo off\n"
        "echo %*>>uv-calls.txt\n"
        f"{failure}\n"
        'echo %* | findstr /C:"pyinstaller" >nul && (\n'
        "  if not exist dist mkdir dist\n"
        "  echo executable>dist\\app.exe\n"
        ")\n"
        "exit /b 0\n",
        encoding="utf-8",
    )


def _run_script(tmp_path: Path, *, fail_on: str | None = None) -> subprocess.CompletedProcess[str]:
    script = tmp_path / SCRIPT.name
    script.write_bytes(SCRIPT.read_bytes())
    _write_fake_uv(tmp_path, fail_on=fail_on)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path};{env['PATH']}"
    env["IMAGEGROUP_NO_PAUSE"] = "1"
    return subprocess.run(
        ["cmd.exe", "/d", "/c", str(script)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )


def test_build_bat_publishes_exe_and_zip_after_checks(tmp_path: Path):
    result = _run_script(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "releases" / "app.exe").read_text().strip() == "executable"
    assert (tmp_path / "releases" / "ImageGroup-portable-win64.zip").is_file()
    calls = (tmp_path / "uv-calls.txt").read_text(encoding="utf-8")
    assert "sync --extra dev" in calls
    assert "run --extra dev pytest -q" in calls
    assert "run --extra dev ruff check src tests" in calls
    assert "run --extra dev pyinstaller --noconfirm --clean packaging\\ImageGroup.spec" in calls


def test_build_bat_stops_without_publishing_when_a_check_fails(tmp_path: Path):
    result = _run_script(tmp_path, fail_on="pytest")

    assert result.returncode != 0
    assert not (tmp_path / "releases" / "app.exe").exists()
