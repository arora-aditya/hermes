from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


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


class ChunkResponse(BaseModel):
    content: str
    score: float
    page_number: Optional[int]
    chunk_index: Optional[int]


class DocumentWithChunksResponse(DocumentResponse):
    chunks: List[ChunkResponse] = []


class SearchRequest(BaseModel):
    query: str
    user_id: int
    chunks_per_document: Optional[int] = 50
    min_score: Optional[float] = 0.7
    sort_by_score: Optional[bool] = True


class DocumentPrefixSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for filename or path")
    similarity_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold for fuzzy matching",
    )


class DocumentPrefixSearchResponse(BaseModel):
    documents: List[DocumentResponse]


class IngestRequest(BaseModel):
    document_ids: List[int] = Field(
        ..., description="List of document IDs to ingest", min_items=1
    )


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
