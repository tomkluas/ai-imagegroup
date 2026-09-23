from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True,slots=True)
class StoredReference:
    content_sha256:str;feature:bytes;model_version:str
class BackendReferenceValidator:
    def __init__(self,backend):self.backend=backend
    def validate(self,path:Path):
        result=self.backend.validate_reference(path)
        return StoredReference(result.content_sha256,result.feature.astype("float32").tobytes(),result.model_version)

