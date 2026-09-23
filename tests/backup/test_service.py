import json,zipfile
import pytest
from image_group.backup.service import BackupError,BackupService
def test_backup_round_trip(tmp_path):
    data=tmp_path/"data";data.mkdir();(data/"data.db").write_bytes(b"db");(data/"reference").mkdir();(data/"reference"/"a.jpg").write_bytes(b"photo")
    archive=BackupService(data).create(tmp_path/"backup.zip"); restored=tmp_path/"restored";BackupService(restored).restore(archive)
    assert (restored/"data.db").read_bytes()==b"db" and (restored/"reference"/"a.jpg").read_bytes()==b"photo"
def test_restore_rejects_path_traversal(tmp_path):
    archive=tmp_path/"bad.zip"
    with zipfile.ZipFile(archive,"w") as z:z.writestr("../outside.txt","bad");z.writestr("manifest.json",json.dumps({"version":1,"files":{}}))
    with pytest.raises(BackupError):BackupService(tmp_path/"data").restore(archive)
def test_restore_rejects_future_version(tmp_path):
    archive=tmp_path/"future.zip"
    with zipfile.ZipFile(archive,"w") as z:z.writestr("manifest.json",json.dumps({"version":999,"files":{}}))
    with pytest.raises(BackupError,match="版本"):BackupService(tmp_path/"data").restore(archive)
