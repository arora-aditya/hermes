from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.sql import func


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)  # User-friendly filename
    file_path = Column(String, nullable=False)  # Local or S3 path
    full_path = Column(String, nullable=False)  # UI path with / separator
    parent_id = Column(
        Integer, ForeignKey("documents.id"), nullable=True
    )  # For folder hierarchy
    is_folder = Column(Boolean, default=False)  # True if this is a folder
    is_ingested = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Self-referential relationship for folder structure
    parent = relationship("Document", remote_side=[id], back_populates="children")
    children = relationship("Document", back_populates="parent")
