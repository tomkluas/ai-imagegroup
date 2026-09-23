from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import numpy as np

from image_group.output.service import OutputService
from image_group.recognition.policy import DecisionPolicy
from image_group.storage.repositories import utc_now
from image_group.tasks.scanner import PhotoScanner


class ClassificationController:
    def __init__(self, database, backend, loader, progress=None):
        self.db, self.backend, self.loader = database, backend, loader
        self.progress = progress or (lambda done, total: None)
        self.outputs = {}
        self.cancel_requested = False

    def cancel(self):
        self.cancel_requested = True

    def _gallery(self, people):
        gallery = {person_id: [] for person_id in people}
        if not people: return gallery
        marks = ",".join("?" for _ in people)
        rows = self.db.execute(f"SELECT person_id,feature FROM reference_photos WHERE status='valid' AND person_id IN ({marks})", tuple(people)).fetchall()
        for row in rows:
            feature = np.frombuffer(row[1], dtype=np.float32).copy(); norm = np.linalg.norm(feature)
            if norm: gallery[row[0]].append(feature / norm)
        return gallery

    def _output(self, task_id):
        output = self.outputs.get(task_id)
        if output is None:
            root = self.db.execute("SELECT output_root FROM tasks WHERE id=?", (task_id,)).fetchone()[0]
            names = {row[0]: row[1] for row in self.db.execute("SELECT id,display_name FROM people").fetchall()}
            output = OutputService(Path(root), names); self.outputs[task_id] = output
        return output

    def start(self, name, paths, output_root, people):
        scan = PhotoScanner().scan([Path(path) for path in paths]); task_id = str(uuid4()); now = utc_now(); self.cancel_requested = False
        self.db.execute("INSERT INTO tasks(id,name,input_kind,output_root,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", (task_id, name, "files", str(output_root), "running", now, now))
        for person_id in people: self.db.execute("INSERT INTO task_people(task_id,person_id) VALUES(?,?)", (task_id, person_id))
        self.outputs[task_id] = OutputService(Path(output_root), {row[0]: row[1] for row in self.db.execute("SELECT id,display_name FROM people")})
        gallery, policy = self._gallery(people), DecisionPolicy()
        for index, photo in enumerate(scan.photos, 1):
            if self.cancel_requested: break
            photo_id = str(uuid4())
            self.db.execute("INSERT INTO task_photos(id,task_id,source_path,content_sha256,status,error) VALUES(?,?,?,?,?,NULL)", (photo_id, task_id, str(photo.path), photo.sha256, "pending"))
            try:
                loaded = self.loader.analysis_image(photo.path, 1280)
                for detected in self.backend.detect_and_embed(loaded.image):
                    match, face_id = policy.classify(detected, gallery), str(uuid4())
                    candidates = [{"person_id": c.person_id, "score": c.score} for c in match.candidates]
                    self.db.execute("INSERT INTO faces(id,task_photo_id,box_json,quality,decision,reason,candidates_json) VALUES(?,?,?,?,?,?,?)", (face_id, photo_id, json.dumps(detected.box), detected.detection_score, match.decision.value, match.reason, json.dumps(candidates)))
                    if match.decision.value == "auto": self._assign(task_id, photo_id, photo.path, face_id, match.candidates[0].person_id, "auto")
                self.db.execute("UPDATE task_photos SET status='recognized',error=NULL WHERE id=?", (photo_id,))
            except Exception as exc:
                self.db.execute("UPDATE task_photos SET status='error',error=? WHERE id=?", (str(exc), photo_id))
            self.progress(index, len(scan.photos))
        status = "cancelled" if self.cancel_requested else ("copy_paused" if self.db.scalar("SELECT count(*) FROM assignments a JOIN task_photos p ON p.id=a.task_photo_id WHERE p.task_id=? AND a.file_status!='copied'", (task_id,)) else "completed")
        self.db.execute("UPDATE tasks SET status=?,updated_at=? WHERE id=?", (status, utc_now(), task_id))
        return task_id

    def _assign(self, task_id, photo_id, source, face_id, person_id, origin):
        assignment_id = str(uuid4())
        self.db.execute("INSERT OR IGNORE INTO assignments(id,task_photo_id,person_id,face_id,source,file_status,output_path,created_at) VALUES(?,?,?,?,?,'pending_copy',NULL,?)", (assignment_id, photo_id, person_id, face_id, origin, utc_now()))
        row = self.db.execute("SELECT id FROM assignments WHERE task_photo_id=? AND person_id=?", (photo_id, person_id)).fetchone()
        assignment_id = row[0]
        try:
            path = self._output(task_id).materialize(task_id, Path(source), [person_id])[0]
            self.db.execute("UPDATE assignments SET file_status='copied',output_path=? WHERE id=?", (str(path), assignment_id))
        except OSError:
            self.db.execute("UPDATE assignments SET file_status='copy_failed' WHERE id=?", (assignment_id,))

    def resume_copies(self, task_id):
        rows = self.db.execute("SELECT a.id,a.person_id,p.source_path FROM assignments a JOIN task_photos p ON p.id=a.task_photo_id WHERE p.task_id=? AND a.file_status!='copied'", (task_id,)).fetchall()
        for row in rows:
            try:
                path = self._output(task_id).materialize(task_id, Path(row[2]), [row[1]])[0]
                self.db.execute("UPDATE assignments SET file_status='copied',output_path=? WHERE id=?", (str(path), row[0]))
            except OSError: continue
        pending = self.db.scalar("SELECT count(*) FROM assignments a JOIN task_photos p ON p.id=a.task_photo_id WHERE p.task_id=? AND a.file_status!='copied'", (task_id,))
        self.db.execute("UPDATE tasks SET status=?,updated_at=? WHERE id=?", ("copy_paused" if pending else "completed", utc_now(), task_id))

    def pending_reviews(self):
        rows = self.db.execute("SELECT f.id,p.source_path,f.box_json,f.candidates_json FROM faces f JOIN task_photos p ON p.id=f.task_photo_id WHERE f.decision='review' ORDER BY p.rowid,f.rowid").fetchall()
        names = {row[0]: row[1] for row in self.db.execute("SELECT id,display_name FROM people")}
        result = []
        for row in rows:
            candidates = [(c["person_id"], names.get(c["person_id"], "已删除"), c["score"]) for c in json.loads(row[3])]
            result.append({"face_id": row[0], "photo_path": Path(row[1]), "box": json.loads(row[2]), "candidates": candidates})
        return result

    def confirm(self, face_id, person_id):
        row = self.db.execute("SELECT p.task_id,p.id,p.source_path FROM faces f JOIN task_photos p ON p.id=f.task_photo_id WHERE f.id=?", (face_id,)).fetchone()
        if row is None: raise LookupError(face_id)
        self._assign(row[0], row[1], row[2], face_id, person_id, "manual")
        self.db.execute("UPDATE faces SET decision='auto',reason='manual_confirmed' WHERE id=?", (face_id,))

    def reject(self, face_id): self.db.execute("UPDATE faces SET decision='rejected',reason='manual_rejected' WHERE id=?", (face_id,))
    def skip(self, face_id): self.db.execute("UPDATE faces SET decision='skipped',reason='manual_skipped' WHERE id=?", (face_id,))


class ResultQueryService:
    def __init__(self, database): self.db = database
    def list_tasks(self): return [dict(row) for row in self.db.execute("SELECT id,name,status,output_root FROM tasks ORDER BY created_at DESC")]
    def list_people(self, task_id):
        rows = self.db.execute("SELECT p.id,p.display_name,count(a.id) FROM people p JOIN assignments a ON a.person_id=p.id JOIN task_photos tp ON tp.id=a.task_photo_id WHERE tp.task_id=? AND a.file_status='copied' GROUP BY p.id,p.display_name ORDER BY p.display_name", (task_id,))
        return [{"id": r[0], "name": r[1], "count": r[2]} for r in rows]
    def list_photos(self, task_id, person_id):
        return [Path(r[0]) for r in self.db.execute("SELECT a.output_path FROM assignments a JOIN task_photos tp ON tp.id=a.task_photo_id WHERE tp.task_id=? AND a.person_id=? AND a.file_status='copied' ORDER BY a.output_path", (task_id, person_id))]
