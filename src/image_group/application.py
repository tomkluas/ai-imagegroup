from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import numpy as np

from image_group.output.service import OutputService
from image_group.recognition.policy import DecisionPolicy
from image_group.storage.database import Database
from image_group.storage.repositories import utc_now
from image_group.tasks.scanner import PhotoScanner


class ClassificationController:
    def __init__(self,database:Database,backend,loader,progress=None):
        self.db,self.backend,self.loader=database,backend,loader;self.progress=progress or (lambda done,total:None);self.outputs={}
    def _gallery(self,people):
        gallery={person_id:[] for person_id in people}
        if not people:return gallery
        marks=",".join("?" for _ in people)
        rows=self.db.execute(f"SELECT person_id,feature FROM reference_photos WHERE status='valid' AND person_id IN ({marks})",tuple(people)).fetchall()
        for row in rows:
            feature=np.frombuffer(row[1],dtype=np.float32).copy();norm=np.linalg.norm(feature)
            if norm:gallery[row[0]].append(feature/norm)
        return gallery
    def start(self,name,paths,output_root,people):
        scan=PhotoScanner().scan([Path(path) for path in paths]);task_id=str(uuid4());now=utc_now()
        self.db.execute("INSERT INTO tasks(id,name,input_kind,output_root,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",(task_id,name,"files",str(output_root),"running",now,now))
        for person_id in people:self.db.execute("INSERT INTO task_people(task_id,person_id) VALUES(?,?)",(task_id,person_id))
        names={row[0]:row[1] for row in self.db.execute("SELECT id,display_name FROM people").fetchall()};output=OutputService(Path(output_root),names);self.outputs[task_id]=output;gallery=self._gallery(people);policy=DecisionPolicy()
        for index,photo in enumerate(scan.photos,1):
            photo_id=str(uuid4());self.db.execute("INSERT INTO task_photos(id,task_id,source_path,content_sha256,status,error) VALUES(?,?,?,?,?,NULL)",(photo_id,task_id,str(photo.path),photo.sha256,"recognized"))
            loaded=self.loader.analysis_image(photo.path,1280)
            for detected in self.backend.detect_and_embed(loaded.image):
                match=policy.classify(detected,gallery);face_id=str(uuid4())
                candidates=[{"person_id":c.person_id,"score":c.score} for c in match.candidates]
                self.db.execute("INSERT INTO faces(id,task_photo_id,box_json,quality,decision,reason,candidates_json) VALUES(?,?,?,?,?,?,?)",(face_id,photo_id,json.dumps(detected.box),detected.detection_score,match.decision.value,match.reason,json.dumps(candidates)))
                if match.decision.value=="auto":self._assign(task_id,photo_id,photo.path,face_id,match.candidates[0].person_id,"auto",output)
            self.progress(index,len(scan.photos))
        self.db.execute("UPDATE tasks SET status='completed',updated_at=? WHERE id=?",(utc_now(),task_id));return task_id
    def _assign(self,task_id,photo_id,source,face_id,person_id,origin,output):
        path=output.materialize(task_id,Path(source),[person_id])[0]
        self.db.execute("INSERT OR IGNORE INTO assignments(id,task_photo_id,person_id,face_id,source,file_status,output_path,created_at) VALUES(?,?,?,?,?,?,?,?)",(str(uuid4()),photo_id,person_id,face_id,origin,"copied",str(path),utc_now()))
    def confirm(self,face_id,person_id):
        row=self.db.execute("SELECT tp.task_id,tp.id,tp.source_path FROM faces f JOIN task_photos tp ON tp.id=f.task_photo_id WHERE f.id=?",(face_id,)).fetchone()
        if row is None:raise LookupError(face_id)
        output=self.outputs.get(row[0]);
        if output is None:
            task=self.db.execute("SELECT output_root FROM tasks WHERE id=?",(row[0],)).fetchone();names={r[0]:r[1] for r in self.db.execute("SELECT id,display_name FROM people").fetchall()};output=OutputService(Path(task[0]),names)
        self._assign(row[0],row[1],Path(row[2]),face_id,person_id,"manual",output);self.db.execute("UPDATE faces SET decision='auto',reason='manual_confirmed' WHERE id=?",(face_id,))

class ResultQueryService:
    def __init__(self,database):self.db=database
    def list_tasks(self):return [dict(row) for row in self.db.execute("SELECT id,name,status FROM tasks ORDER BY created_at DESC").fetchall()]
    def list_people(self,task_id):
        rows=self.db.execute("SELECT p.id,p.display_name,count(a.id) FROM people p JOIN assignments a ON a.person_id=p.id JOIN task_photos tp ON tp.id=a.task_photo_id WHERE tp.task_id=? GROUP BY p.id,p.display_name ORDER BY p.display_name",(task_id,)).fetchall()
        return [{"id":r[0],"name":r[1],"count":r[2]} for r in rows]
    def list_photos(self,task_id,person_id):
        rows=self.db.execute("SELECT a.output_path FROM assignments a JOIN task_photos tp ON tp.id=a.task_photo_id WHERE tp.task_id=? AND a.person_id=? ORDER BY a.output_path",(task_id,person_id)).fetchall();return [Path(r[0]) for r in rows]
