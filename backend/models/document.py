from sqlalchemy import Column, Integer, String, Boolean, DateTime
from .base import Base
from sqlalchemy.sql import func


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)  # User-friendly filename
    file_path = Column(String, nullable=False)  # Local or S3 path
    is_ingested = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
