from pathlib import Path

import PySide6

root = Path(SPECPATH).parent
pyside_root = Path(PySide6.__file__).parent
pyside_binaries = [
    (str(pyside_root / "concrt140.dll"), "PySide6"),
    (str(pyside_root / "msvcp140_codecvt_ids.dll"), "PySide6"),
]
datas = [
    (str(root / "resources/models"), "resources/models"),
    (str(root / "docs/user-guide.md"), "docs"),
    (str(root / "THIRD_PARTY_NOTICES.md"), "."),
]
a = Analysis(
    [str(root / "src/image_group/app.py")],
    pathex=[str(root / "src")],
    binaries=pyside_binaries,
    datas=datas,
    hiddenimports=[
        "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets",
        "cv2", "numpy", "PIL", "psutil",
    ],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)

# Qt for Windows uses the operating system ICU. A developer PATH can contain
# unrelated Poppler ICU DLLs; bundling those produces entry-point error 127.
foreign_icu = {"icuuc.dll", "icudt78.dll"}
a.binaries = [entry for entry in a.binaries if Path(entry[0]).name.lower() not in foreign_icu]

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,
    name="园区照片分类助手",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
