from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, UUID4
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.conversation import Message, ConversationHistory
from uuid import UUID
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage
from chat.conversation import ConversationService


class ChatRequest(BaseModel):
    message: str
    conversation_id: UUID4 | None = None
    user_id: str


class ChatResponse(BaseModel):
    message: str
    conversation_id: UUID4


class Agent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-exp"),
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=os.environ.get("GEMINI_API_KEY"),
        )
        self.llm = FakeListChatModel(
            responses=["This is a test response from the fake chat model."]
        )
        self.system_prompt = {
            "role": "system",
            "content": os.getenv("GEMINI_SYSTEM_PROMPT"),
        }

    async def chat(self, request: ChatRequest, db: AsyncSession):
        # Get messages prepared for LLM
        messages = await ConversationService.prepare_messages_for_llm(
            db, request.conversation_id, self.system_prompt
        )

        # Get response from the model
        response = self.llm.invoke(messages)

        # Process the complete chat interaction
        conversation = await ConversationService.process_chat_interaction(
            db=db,
            user_id=request.user_id,
            message=request.message,
            conversation_id=request.conversation_id,
            system_prompt=self.system_prompt,
            llm_response=response.content,
        )

        return ChatResponse(
            message=response.content, conversation_id=conversation.conversation_id
        )
