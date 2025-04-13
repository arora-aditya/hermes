import os
from typing import AsyncGenerator

from chat.conversation import ConversationService
from langchain.prompts import ChatPromptTemplate
from schemas.streaming import EventType, StreamEvent
from sqlalchemy.ext.asyncio import AsyncSession
from utils.llm import get_gemini_llm


class StreamingAgent:
    def __init__(self):
        self.llm = get_gemini_llm()
        self.system_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    os.getenv(
                        "GEMINI_SYSTEM_PROMPT", "You are a helpful AI assistant."
                    ),
                ),
                ("human", "{input}"),
            ]
        )

    async def stream_chat(
        self, message: str, conversation_id: str | None = None
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream a chat response directly from the LLM without RAG.
        This is a simpler version that just demonstrates streaming capabilities.
        """
        # Signal that we're starting to think
        yield StreamEvent(event=EventType.THINKING_START, data="Preparing response...")

        # Stream the response from the LLM
        async for event in self.llm.astream_events(
            message,
            version="v2",
            config={"metadata": {"session_id": conversation_id}},
        ):
            if event["event"] == "on_chat_model_start":
                yield StreamEvent(
                    event=EventType.THINKING_START,
                    data="Starting to generate response...",
                )
            elif event["event"] == "on_chat_model_stream":
                yield StreamEvent(
                    event=EventType.TOKEN, data=event["data"]["chunk"].content
                )
            elif event["event"] == "on_chat_model_end":
                yield StreamEvent(event=EventType.COMPLETE, data="Response complete")

    async def stream_chat_with_history(
        self,
        message: str,
        db: AsyncSession,
        user_id: str,
        conversation_id: str | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream a chat response with conversation history support.
        This version will save the conversation to the database.
        """
        # First stream the response
        response_chunks = []
        async for event in self.stream_chat(message, conversation_id):
            if event.event == EventType.TOKEN:
                response_chunks.append(event.data)
            yield event

        # After streaming is complete, save to database
        full_response = "".join(response_chunks)
        await ConversationService.process_chat_interaction(
            db=db,
            user_id=user_id,
            message=message,
            conversation_id=conversation_id,
            system_prompt={"role": "system", "content": self.system_prompt},
            llm_response=full_response,
        )
