from pydantic import UUID4, BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: UUID4 | None = None
    user_id: str


class ChatResponse(BaseModel):
    message: str
    conversation_id: UUID4
