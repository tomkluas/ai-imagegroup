from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Any

SCHEMA_V1="""
CREATE TABLE people (id TEXT PRIMARY KEY,display_name TEXT NOT NULL COLLATE NOCASE UNIQUE,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE reference_photos (id TEXT PRIMARY KEY,person_id TEXT NOT NULL REFERENCES people(id) ON DELETE CASCADE,source_path TEXT NOT NULL,managed_path TEXT NOT NULL UNIQUE,content_sha256 TEXT NOT NULL,status TEXT NOT NULL,feature BLOB,model_version TEXT,created_at TEXT NOT NULL);
CREATE INDEX idx_reference_photos_person ON reference_photos(person_id);
CREATE TABLE tasks (id TEXT PRIMARY KEY,name TEXT NOT NULL,input_kind TEXT NOT NULL,output_root TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE task_people (task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,person_id TEXT NOT NULL REFERENCES people(id),PRIMARY KEY(task_id,person_id));
CREATE TABLE task_photos (id TEXT PRIMARY KEY,task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,source_path TEXT NOT NULL,content_sha256 TEXT NOT NULL,status TEXT NOT NULL,error TEXT,UNIQUE(task_id,content_sha256));
CREATE INDEX idx_task_photos_task ON task_photos(task_id);
CREATE TABLE faces (id TEXT PRIMARY KEY,task_photo_id TEXT NOT NULL REFERENCES task_photos(id) ON DELETE CASCADE,box_json TEXT NOT NULL,quality REAL NOT NULL,decision TEXT NOT NULL,reason TEXT NOT NULL,candidates_json TEXT NOT NULL);
CREATE TABLE assignments (id TEXT PRIMARY KEY,task_photo_id TEXT NOT NULL REFERENCES task_photos(id) ON DELETE CASCADE,person_id TEXT NOT NULL REFERENCES people(id),face_id TEXT REFERENCES faces(id) ON DELETE SET NULL,source TEXT NOT NULL,file_status TEXT NOT NULL,output_path TEXT,created_at TEXT NOT NULL,UNIQUE(task_photo_id,person_id));
CREATE INDEX idx_assignments_person ON assignments(person_id);
PRAGMA user_version=1;
"""
class Database:
 def __init__(self,path:Path)->None:
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self._lock=RLock();self._connection=sqlite3.connect(self.path,isolation_level=None,check_same_thread=False);self._connection.row_factory=sqlite3.Row;self._connection.execute("PRAGMA foreign_keys=ON");self._connection.execute("PRAGMA journal_mode=WAL");self._connection.execute("PRAGMA busy_timeout=5000")
 def migrate(self)->None:
  version=int(self.scalar("PRAGMA user_version"))
  if version==0:
   with self.transaction():self._connection.executescript(SCHEMA_V1)
  elif version!=1:raise RuntimeError(f"不支持的数据库版本: {version}")
 @contextmanager
 def transaction(self)->Iterator[None]:
  with self._lock:
   self._connection.execute("BEGIN IMMEDIATE")
   try:yield
   except BaseException:self._connection.rollback();raise
   else:self._connection.commit()
 def execute(self,sql:str,parameters:tuple[Any,...]=())->sqlite3.Cursor:
  with self._lock:return self._connection.execute(sql,parameters)
 def scalar(self,sql:str,parameters:tuple[Any,...]=())->Any:
  row=self.execute(sql,parameters).fetchone();return None if row is None else row[0]
 def table_names(self)->set[str]:return {str(row[0]) for row in self.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
 def close(self)->None:
  with self._lock:self._connection.close()
