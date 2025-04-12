from sqlalchemy import ARRAY, Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)  # User-friendly filename
    path_array = Column(
        ARRAY(String), nullable=False, server_default="{}"
    )  # Directory hierarchy
    file_path = Column(String, nullable=False)  # Local or S3 path
    is_ingested = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
