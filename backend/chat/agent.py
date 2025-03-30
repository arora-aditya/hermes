from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, UUID4
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.conversation import Message, ConversationHistory
from uuid import UUID


class ConversationRequest(BaseModel):
    conversation_id: UUID4


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
        self.system_prompt = {
            "role": "system",
            "content": os.getenv("GEMINI_SYSTEM_PROMPT"),
        }

    async def save_message(
        self, db: AsyncSession, content: str, role: str, conversation_id: UUID
    ) -> Message:
        message = Message(conversation_id=conversation_id, content=content, role=role)
        db.add(message)
        await db.flush()  # This will populate the message_id
        return message

    async def get_or_create_conversation(
        self, db: AsyncSession, user_id: str, conversation_id: UUID | None = None
    ) -> ConversationHistory:
        if conversation_id:
            # Try to find existing conversation
            stmt = select(ConversationHistory).where(
                ConversationHistory.conversation_id == conversation_id,
                ConversationHistory.user_id == user_id,
            )
            result = await db.execute(stmt)
            conversation = result.scalar_one_or_none()

            if not conversation:
                # Create new conversation with provided UUID
                conversation = ConversationHistory(
                    user_id=user_id, conversation_id=conversation_id
                )
                db.add(conversation)
                await db.flush()
        else:
            # Create new conversation with auto-generated UUID
            conversation = ConversationHistory(user_id=user_id)
            db.add(conversation)
            await db.flush()

        return conversation

    async def get_conversations(
        self, db: AsyncSession, user_id: str
    ) -> list[ConversationHistory]:
        stmt = select(ConversationHistory).where(ConversationHistory.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_conversation_messages(
        self, db: AsyncSession, conversation: ConversationRequest
    ) -> list[Message]:
        # Get all messages for the conversation ordered by message_id
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation.conversation_id)
            .order_by(Message.message_id)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def chat(self, request: ChatRequest, db: AsyncSession):
        # Get or create conversation
        conversation = await self.get_or_create_conversation(
            db, request.user_id, request.conversation_id
        )

        # Save user message
        user_message = await self.save_message(
            db,
            content=request.message,
            role="user",
            conversation_id=conversation.conversation_id,
        )

        # Get all messages from the conversation history
        conversation_messages = await self.get_conversation_messages(
            db, ConversationRequest(conversation_id=conversation.conversation_id)
        )

        # Prepare messages for the model
        messages = [self.system_prompt]  # Start with system prompt
        messages.extend(
            [
                {"role": msg.role, "content": msg.content}
                for msg in conversation_messages
            ]
        )
        # Get response from the model
        response = self.llm.invoke(messages)

        # Save assistant message
        assistant_message = await self.save_message(
            db,
            content=response.content,
            role="assistant",
            conversation_id=conversation.conversation_id,
        )

        # Update conversation with last message
        conversation.last_message_id = assistant_message.message_id
        await db.commit()

        return ChatResponse(
            message=response.content, conversation_id=conversation.conversation_id
        )
