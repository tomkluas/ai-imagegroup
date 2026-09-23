from pathlib import Path

root = Path(SPECPATH).parent
datas = [
    (str(root / "resources/models"), "resources/models"),
    (str(root / "docs/user-guide.md"), "docs"),
    (str(root / "THIRD_PARTY_NOTICES.md"), "."),
]
a = Analysis([str(root / "src/image_group/app.py")], pathex=[str(root / "src")], binaries=[], datas=datas, hiddenimports=["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets", "cv2", "numpy", "PIL", "psutil"], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="园区照片分类助手", debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="园区照片分类助手")
