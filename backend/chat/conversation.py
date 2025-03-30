from pydantic import BaseModel, UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models.conversation import Message, ConversationHistory
from uuid import UUID
from fastapi import HTTPException
from typing import List, Dict


class ConversationService:
    @staticmethod
    async def create_conversation(
        db: AsyncSession, user_id: str, conversation_id: UUID | None = None
    ) -> ConversationHistory:
        """Create a new conversation or get existing one if conversation_id is provided."""
        if conversation_id:
            # Check if conversation exists and belongs to user
            stmt = select(ConversationHistory).where(
                ConversationHistory.conversation_id == conversation_id,
                ConversationHistory.user_id == user_id,
            )
            result = await db.execute(stmt)
            conversation = result.scalar_one_or_none()

            if conversation:
                return conversation

            # Create new conversation with provided UUID
            conversation = ConversationHistory(
                user_id=user_id, conversation_id=conversation_id
            )
        else:
            # Create new conversation with auto-generated UUID
            conversation = ConversationHistory(user_id=user_id)
        db.add(conversation)
        await db.commit()
        return conversation

    @staticmethod
    async def list_conversations(
        db: AsyncSession, user_id: str
    ) -> List[ConversationHistory]:
        """Get all conversations for a user."""
        stmt = (
            select(ConversationHistory)
            .where(ConversationHistory.user_id == user_id)
            .order_by(ConversationHistory.created_at.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_conversation_messages(
        db: AsyncSession, conversation_id: UUID
    ) -> List[Message]:
        """Get all messages for a conversation."""
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.message_id)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def add_message(
        db: AsyncSession, content: str, role: str, conversation_id: UUID
    ) -> Message:
        """Add a new message to a conversation."""
        # Verify conversation exists
        stmt = select(ConversationHistory).where(
            ConversationHistory.conversation_id == conversation_id
        )
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        message = Message(conversation_id=conversation_id, content=content, role=role)
        db.add(message)

        # Update conversation's last message
        conversation.last_message_id = message.message_id

        await db.flush()
        return message

    @staticmethod
    async def delete_conversation(db: AsyncSession, conversation_id: UUID) -> bool:
        """Delete a conversation and all its messages."""
        # Verify conversation exists and belongs to user
        stmt = select(ConversationHistory).where(
            ConversationHistory.conversation_id == conversation_id,
        )
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Delete all messages first
        await db.execute(
            delete(Message).where(Message.conversation_id == conversation_id)
        )

        # Delete the conversation
        await db.execute(
            delete(ConversationHistory).where(
                ConversationHistory.conversation_id == conversation_id
            )
        )

        await db.flush()
        return True

    @staticmethod
    async def prepare_messages_for_llm(
        db: AsyncSession, conversation_id: UUID, system_prompt: Dict[str, str]
    ) -> List[Dict[str, str]]:
        """Prepare messages for LLM including system prompt and conversation history."""
        # Get conversation history
        conversation_messages = await ConversationService.get_conversation_messages(
            db, conversation_id
        )

        # Prepare messages for the model
        messages = [system_prompt]  # Start with system prompt
        messages.extend(
            [
                {"role": msg.role, "content": msg.content}
                for msg in conversation_messages
            ]
        )

        return messages

    @staticmethod
    async def process_chat_interaction(
        db: AsyncSession,
        user_id: str,
        message: str,
        conversation_id: UUID | None,
        system_prompt: Dict[str, str],
        llm_response: str,
    ) -> ConversationHistory:
        """Process a complete chat interaction including saving messages and managing conversation."""
        # Get or create conversation
        conversation = await ConversationService.create_conversation(
            db, user_id, conversation_id
        )

        # Save user message
        await ConversationService.add_message(
            db,
            content=message,
            role="user",
            conversation_id=conversation.conversation_id,
        )

        # Save assistant message
        await ConversationService.add_message(
            db,
            content=llm_response,
            role="assistant",
            conversation_id=conversation.conversation_id,
        )

        await db.commit()
        return conversation
