from models.base import Base
from sqlalchemy import ARRAY, Boolean, Column, DateTime, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)  # User-friendly filename
    path_array = Column(
        ARRAY(String), nullable=False, server_default="{}"
    )  # Directory hierarchy
    path_ltree = Column(String, nullable=False)  # Will store ltree path
    file_path = Column(String, nullable=False)  # Local or S3 path
    is_ingested = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes for efficient searching
    __table_args__ = (
        Index(
            "idx_document_filename_trgm",
            "filename",
            postgresql_using="gin",
            postgresql_ops={"filename": "gin_trgm_ops"},
        ),
        Index("idx_document_path_ltree", "path_ltree", postgresql_using="gist"),
    )
