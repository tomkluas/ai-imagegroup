from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from uuid import uuid4


class BackupError(ValueError):pass
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def is_sqlite(path):
 try:
  with Path(path).open("rb") as stream:return stream.read(16)==b"SQLite format 3\x00"
 except OSError:return False
class BackupService:
 version=1
 def __init__(self,data_root:Path):self.data_root=Path(data_root)
 def create(self,archive:Path)->Path:
  archive=Path(archive);archive.parent.mkdir(parents=True,exist_ok=True);files={};snapshot=Path(tempfile.mkdtemp(prefix="backup-",dir=archive.parent))
  try:
   if self.data_root.exists():
    for path in self.data_root.rglob("*"):
     if path.is_file() and path.name not in {"data.db","data.db-wal","data.db-shm"}:
      target=snapshot/path.relative_to(self.data_root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    database=self.data_root/"data.db"
    if database.exists():
     if is_sqlite(database):
      source=sqlite3.connect(database);target=sqlite3.connect(snapshot/"data.db")
      try:source.backup(target)
      finally:target.close();source.close()
     else:shutil.copy2(database,snapshot/"data.db")
   with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as bundle:
    for path in sorted(p for p in snapshot.rglob("*") if p.is_file()):
     name=path.relative_to(snapshot).as_posix();files[name]=digest(path);bundle.write(path,name)
    bundle.writestr("manifest.json",json.dumps({"version":self.version,"files":files},ensure_ascii=False))
   return archive
  finally:shutil.rmtree(snapshot,ignore_errors=True)
 @staticmethod
 def _safe_name(raw:str)->PurePosixPath:
  normalized=raw.replace("\\","/")
  if normalized.startswith("/") or re.match(r"^[A-Za-z]:",normalized):raise BackupError("备份包含不安全路径")
  name=PurePosixPath(normalized)
  if not normalized or name.is_absolute() or ".." in name.parts:raise BackupError("备份包含不安全路径")
  return name
 def inspect(self,archive:Path):
  with zipfile.ZipFile(archive) as bundle:
   for info in bundle.infolist():self._safe_name(info.filename)
   try:manifest=json.loads(bundle.read("manifest.json"))
   except Exception as exc:raise BackupError("备份清单损坏") from exc
   if manifest.get("version",0)>self.version:raise BackupError("备份版本高于当前程序")
   for name,expected in manifest.get("files",{}).items():
    self._safe_name(name)
    if hashlib.sha256(bundle.read(name)).hexdigest()!=expected:raise BackupError(f"文件校验失败: {name}")
   return manifest
 def restore(self,archive:Path)->None:
  manifest=self.inspect(archive);self.data_root.parent.mkdir(parents=True,exist_ok=True);staging=Path(tempfile.mkdtemp(prefix="restore-",dir=self.data_root.parent));previous=self.data_root.parent/f".{self.data_root.name}.previous-{uuid4().hex}"
  try:
   with zipfile.ZipFile(archive) as bundle:
    for name in manifest.get("files",{}):
     target=staging/self._safe_name(name)
     if not target.resolve().is_relative_to(staging.resolve()):raise BackupError("备份包含不安全路径")
     target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(bundle.read(name))
   database=staging/"data.db"
   if is_sqlite(database):
    connection=sqlite3.connect(database)
    try:
     for reference_id,managed in connection.execute("SELECT id,managed_path FROM reference_photos").fetchall():connection.execute("UPDATE reference_photos SET managed_path=? WHERE id=?",(str(self.data_root/"reference"/Path(managed).name),reference_id))
     connection.commit()
    finally:connection.close()
   had_current=self.data_root.exists()
   if had_current:self.data_root.replace(previous)
   try:staging.replace(self.data_root)
   except BaseException:
    if had_current and previous.exists():previous.replace(self.data_root)
    raise
   if previous.exists():shutil.rmtree(previous)
  except BaseException:shutil.rmtree(staging,ignore_errors=True);raise
