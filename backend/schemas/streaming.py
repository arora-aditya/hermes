from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class EventType(str, Enum):
    SEARCH_START = "search_start"
    SEARCH_COMPLETE = "search_complete"
    THINKING_START = "thinking_start"
    THINKING_COMPLETE = "thinking_complete"
    TOKEN = "token"
    COMPLETE = "complete"
    ERROR = "error"


class SearchResult(BaseModel):
    """Represents a search result for streaming purposes"""

    document_id: str
    score: float
    content: str


class StreamEvent(BaseModel):
    event: EventType
    data: str
    metadata: Optional[Dict] = None


class StreamingChatRequest(BaseModel):
    message: str
    user_id: str
    conversation_id: str | None = None
