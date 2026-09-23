from pathlib import Path

from image_group.people.adapter import BackendReferenceValidator
from image_group.people.service import PeopleService
from image_group.recognition.opencv_backend import OpenCvRecognitionBackend
from image_group.storage.database import Database
from image_group.storage.repositories import PersonRepository


def test_real_sface_feature_is_stored_as_float32_blob(tmp_path):
    root=Path(__file__).parents[2];db=Database(tmp_path/"data.db");db.migrate();backend=OpenCvRecognitionBackend(root/"resources"/"models")
    service=PeopleService(db,PersonRepository(db),tmp_path/"refs",BackendReferenceValidator(backend));person=service.create_person("测试儿童")
    service.import_reference(person.id,root/"tests"/"fixtures"/"lena.jpg")
    feature=db.execute("SELECT feature FROM reference_photos").fetchone()[0]
    assert isinstance(feature,bytes) and len(feature)>0 and len(feature)%4==0

