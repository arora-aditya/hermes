from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(
        Integer, primary_key=True, autoincrement=True
    )  # Make this the primary key
    conversation_id = Column(
        UUID(as_uuid=True), nullable=False
    )  # To group messages in a conversation
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)  # External user ID
    conversation_id = Column(
        UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4
    )  # Unique conversation identifier
    last_message_id = Column(
        Integer, ForeignKey("messages.message_id"), nullable=True
    )  # Latest message in conversation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
