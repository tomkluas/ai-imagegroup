import numpy as np

from image_group.application import ClassificationController, ResultQueryService
from image_group.recognition.base import DetectedFace
from image_group.storage.database import Database
from image_group.storage.repositories import PersonRepository


class Backend:
    def detect_and_embed(self,image): return [DetectedFace((1,2,80,80),(),.9,80,np.array([1.,0.],np.float32))]
class Loader:
    def analysis_image(self,path,max_long_edge): return type("Loaded",(),{"image":np.zeros((10,10,3),np.uint8)})()
def test_end_to_end_auto_classification_creates_result_and_history(tmp_path):
    db=Database(tmp_path/"data.db");db.migrate();people=PersonRepository(db);person=people.create("张小明")
    db.execute("INSERT INTO reference_photos(id,person_id,source_path,managed_path,content_sha256,status,feature,model_version,created_at) VALUES(?,?,?,?,?,?,?,?,?)",("r1",person.id,"x","x2","h","valid",np.array([1.,0.],np.float32).tobytes(),"m","2026"))
    source=tmp_path/"input"/"活动.jpg";source.parent.mkdir();source.write_bytes(b"photo")
    controller=ClassificationController(db,Backend(),Loader())
    task_id=controller.start("今天",[source],tmp_path/"out",[person.id])
    query=ResultQueryService(db)
    assert query.list_people(task_id)[0]["name"]=="张小明"
    result=query.list_photos(task_id,person.id)[0]
    assert result.exists() and result.read_bytes()==b"photo"
