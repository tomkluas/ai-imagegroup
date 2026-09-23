from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


class BackupError(ValueError):pass
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
class BackupService:
    version=1
    def __init__(self,data_root:Path):self.data_root=Path(data_root)
    def create(self,archive:Path)->Path:
        archive=Path(archive);archive.parent.mkdir(parents=True,exist_ok=True);files={}
        with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as bundle:
            if self.data_root.exists():
                for path in sorted(p for p in self.data_root.rglob("*") if p.is_file()):
                    name=path.relative_to(self.data_root).as_posix();files[name]=digest(path);bundle.write(path,name)
            bundle.writestr("manifest.json",json.dumps({"version":self.version,"files":files},ensure_ascii=False))
        return archive
    def inspect(self,archive:Path):
        with zipfile.ZipFile(archive) as bundle:
            for info in bundle.infolist():
                name=PurePosixPath(info.filename)
                if name.is_absolute() or ".." in name.parts:raise BackupError("备份包含不安全路径")
            try:manifest=json.loads(bundle.read("manifest.json"))
            except Exception as exc:raise BackupError("备份清单损坏") from exc
            if manifest.get("version",0)>self.version:raise BackupError("备份版本高于当前程序")
            for name,expected in manifest.get("files",{}).items():
                if hashlib.sha256(bundle.read(name)).hexdigest()!=expected:raise BackupError(f"文件校验失败: {name}")
            return manifest
    def restore(self,archive:Path)->None:
        manifest=self.inspect(archive);self.data_root.parent.mkdir(parents=True,exist_ok=True)
        staging=Path(tempfile.mkdtemp(prefix="restore-",dir=self.data_root.parent))
        try:
            with zipfile.ZipFile(archive) as bundle:
                for name in manifest.get("files",{}):
                    target=staging/PurePosixPath(name);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(bundle.read(name))
            if self.data_root.exists():shutil.rmtree(self.data_root)
            staging.replace(self.data_root)
        except BaseException:
            shutil.rmtree(staging,ignore_errors=True);raise
