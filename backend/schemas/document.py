from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    filename: str
    path_array: List[str]


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: int
    is_ingested: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DirectoryNode(BaseModel):
    type: str  # "directory" or "file"
    name: str
    path: List[str]
    children: Optional[List["DirectoryNode"]] = None
    document: Optional[DocumentResponse] = None


class DirectoryTreeResponse(BaseModel):
    type: str = "directory"
    name: str = "root"
    path: List[str] = []
    children: List[DirectoryNode]
