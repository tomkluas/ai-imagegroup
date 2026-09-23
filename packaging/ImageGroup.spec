from pathlib import Path
root=Path(SPECPATH).parent
a=Analysis([str(root/'src/image_group/app.py')],pathex=[str(root/'src')],binaries=[],datas=[(str(root/'resources/models'),'resources/models')],hiddenimports=['PySide6.QtCore','PySide6.QtGui','PySide6.QtWidgets','cv2','numpy','PIL','psutil'],hookspath=[],hooksconfig={},runtime_hooks=[],excludes=[],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='园区照片分类助手',debug=False,bootloader_ignore_signals=False,strip=False,upx=False,console=False)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='园区照片分类助手')
