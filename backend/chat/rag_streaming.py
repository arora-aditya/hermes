import json
import os
from typing import AsyncGenerator, Dict, List
from uuid import UUID

from chat.conversation import ConversationService
from chat.streaming import StreamingAgent
from chat.tools import create_streaming_search_tool
from fastapi.responses import StreamingResponse
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate
from langchain_core.documents import Document as LangchainDocument
from models.conversation import ConversationHistory
from schemas.conversation import ChatRequest
from schemas.streaming import EventType, SearchResult, StreamEvent, StreamingChatRequest
from sqlalchemy.ext.asyncio import AsyncSession


def convert_langchain_doc_to_search_result(doc: LangchainDocument) -> Dict:
    """Convert a Langchain document to a standardized search result format."""
    return {
        "document_id": doc.metadata.get("document_id", "unknown"),
        "content": doc.page_content,
        "score": doc.metadata.get("score", 0.0),
    }


class RAGStreamingAgent(StreamingAgent):
    """
    Streaming agent with RAG (Retrieval Augmented Generation) capabilities.
    Extends the base StreamingAgent to add document search and context integration.
    """

    def __init__(self):
        super().__init__()
        # Override the system prompt to include RAG context
        self.system_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", os.getenv("GEMINI_SYSTEM_PROMPT")),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

    async def create_streaming_response(
        self, request: StreamingChatRequest, db_session: AsyncSession
    ) -> StreamingResponse:
        """
        Create a streaming response for RAG chat using Server-Sent Events (SSE).
        This method handles the streaming response setup and event generation.

        Args:
            request (StreamingChatRequest): The chat request containing message and user details
            db_session (AsyncSession): Database session for data access

        Returns:
            StreamingResponse: A FastAPI StreamingResponse configured for SSE
        """

        async def event_generator():
            async for event in self.stream_rag_chat(
                message=request.message,
                db=db_session,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
            ):
                yield f"data: {json.dumps(event.dict())}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    async def _stream_search_results(
        self, search_tool, query: str
    ) -> AsyncGenerator[tuple[StreamEvent, List[Dict]], None]:
        """Stream search results and yield both events and the results."""
        yield StreamEvent(
            event=EventType.SEARCH_START,
            data="Searching through documents...",
        ), []

        try:
            # Execute search with proper query parameter
            search_results = await search_tool.ainvoke({"query": query})

            if not search_results:
                yield StreamEvent(
                    event=EventType.SEARCH_COMPLETE,
                    data="No relevant documents found",
                    metadata={"count": 0},
                ), []
            else:
                # Process document objects
                processed_results = [
                    convert_langchain_doc_to_search_result(doc)
                    for doc in search_results
                ]

                yield StreamEvent(
                    event=EventType.SEARCH_COMPLETE,
                    data=f"Found {len(processed_results)} relevant documents",
                    metadata={"count": len(processed_results)},
                ), processed_results

        except Exception as e:
            # Log the error for debugging but return a user-friendly message
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Search error: {str(e)}", exc_info=True)

            yield StreamEvent(
                event=EventType.ERROR,
                data="Unable to search documents at this time. Please try again later.",
                metadata={"error_type": "search_error"},
            ), []

    async def stream_rag_chat(
        self,
        message: str,
        db: AsyncSession,
        user_id: str,
        conversation_id: UUID | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream a chat response with RAG integration.
        This version includes document search and context integration.
        """
        try:
            # Create streaming search tool
            search_tool = create_streaming_search_tool(user_id=user_id, db=db)

            # Create agent executor
            agent = create_tool_calling_agent(
                llm=self.llm,
                tools=[search_tool],
                prompt=self.system_prompt,
            )

            agent_executor = AgentExecutor(
                agent=agent,
                tools=[search_tool],
                verbose=True,
                return_intermediate_steps=True,
            )

            # Create a proper ChatRequest object
            chat_request = ChatRequest(
                message=message, user_id=user_id, conversation_id=conversation_id
            )

            # Get conversation history
            messages = await ConversationService.prepare_messages_for_llm(
                db=db,
                request=chat_request,
                system_prompt={
                    "role": "system",
                    "content": os.getenv(
                        "GEMINI_SYSTEM_PROMPT", "You are a helpful AI assistant."
                    ),
                },
            )

            # Stream search results
            search_results = []
            async for event, results in self._stream_search_results(
                search_tool, message
            ):
                yield event
                if results:
                    search_results = results

            # If we encountered a search error, end the stream here
            if event.event == EventType.ERROR:
                return

            # Signal start of thinking
            yield StreamEvent(
                event=EventType.THINKING_START,
                data="Processing search results and generating response...",
            )

            # Collect response chunks for saving to database
            response_chunks = []
            thinking_complete_sent = False

            # Stream the agent's response
            async for event in agent_executor.astream_events(
                {
                    "input": message,
                    "chat_history": messages[
                        1:-1
                    ],  # Exclude system prompt and current message
                },
                version="v2",
                config={
                    "metadata": {
                        "session_id": str(conversation_id) if conversation_id else None,
                        "search_results": search_results,
                    }
                },
            ):
                if event["event"] == "on_chat_model_stream":
                    # Send thinking complete before first token if not sent
                    if not thinking_complete_sent:
                        yield StreamEvent(
                            event=EventType.THINKING_COMPLETE,
                            data="Finished processing, starting response...",
                        )
                        thinking_complete_sent = True

                    chunk = event["data"]["chunk"].content
                    if chunk.strip():  # Only append and yield non-empty chunks
                        response_chunks.append(chunk)
                        yield StreamEvent(event=EventType.TOKEN, data=chunk)
                elif event["event"] == "on_chat_model_end":
                    # Only send complete event at the very end
                    if response_chunks:  # Only if we actually had a response
                        yield StreamEvent(
                            event=EventType.COMPLETE,
                            data="Response complete",
                            metadata={"search_result_count": len(search_results)},
                        )

            # Save the complete interaction to the database
            if response_chunks:  # Only save if we have a response
                full_response = "".join(response_chunks)
                await ConversationService.process_chat_interaction(
                    db=db,
                    user_id=user_id,
                    message=message,
                    conversation_id=conversation_id,
                    system_prompt={"role": "system", "content": self.system_prompt},
                    llm_response=full_response,
                )

        except Exception as e:
            # Log the error for debugging
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Stream chat error: {str(e)}", exc_info=True)

            # Return a user-friendly error
            yield StreamEvent(
                event=EventType.ERROR,
                data="An error occurred while processing your request. Please try again later.",
                metadata={"error_type": "general_error"},
            )
