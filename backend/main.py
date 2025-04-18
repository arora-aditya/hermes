import logging
import time
from contextlib import asynccontextmanager
from typing import List
from uuid import UUID

import load_env
import uvicorn
from chat.agent import Agent, ChatRequest
from chat.conversation import ConversationService
from chat.rag_streaming import RAGStreamingAgent
from controller import documents, organizations, search, users
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from models.relationships import setup_relationships
from schemas.streaming import StreamingChatRequest
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database import get_db
from utils.logging_config import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    try:
        if not load_env.IS_ENV_LOADED:
            logger.error("Environment variables not loaded")
            raise Exception("Environment variables not loaded")

        logger.info("Starting application initialization")

        # Set up SQLAlchemy relationships
        setup_relationships()
        logger.info("Database relationships configured")

        logger.info("Application startup complete")
        yield

        # Shutdown
        logger.info("Application shutdown initiated")
    except Exception as e:
        logger.error(f"Error during application lifecycle: {str(e)}", exc_info=True)
        raise


# Initialize FastAPI app
app = FastAPI(
    title="Hermes API",
    description="Document processing and search API",
    version="1.0.0",
    lifespan=lifespan,
)


# Add middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests and their processing time."""
    start_time = time.time()

    # Generate request ID
    request_id = str(time.time())
    logger.info(
        f"Request started - ID: {request_id} - Method: {request.method} - URL: {request.url}"
    )

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Request completed - ID: {request_id} - Status: {response.status_code} - Duration: {process_time:.2f}ms"
        )
        return response
    except Exception as e:
        logger.error(
            f"Request failed - ID: {request_id} - Error: {str(e)}", exc_info=True
        )
        raise


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
logger.debug("Registering API routes")
app.include_router(users.router, prefix="/api")
app.include_router(organizations.router, prefix="/api")
app.include_router(documents.router)  # Documents router already has /api prefix
app.include_router(search.router)  # Search router already has /api prefix
logger.debug("API routes registered successfully")


@app.get("/")
def read_root():
    """Health check endpoint."""
    logger.debug("Health check request received")
    return {"status": "healthy", "service": "Hermes API"}


# Initialize agents
agent = Agent()
rag_streaming_agent = RAGStreamingAgent()


@app.post("/api/chat")
async def chat(request: ChatRequest, db_session: AsyncSession = Depends(get_db)):
    return await agent.chat(request, db_session)


@app.post("/api/chat/conversation/{user_id}")
async def create_conversation(user_id: str, db_session: AsyncSession = Depends(get_db)):
    return await ConversationService.create_conversation(db_session, user_id)


@app.get("/api/chat/conversation/{conversation_id}")
async def get_conversation_messages(
    conversation_id: UUID, db_session: AsyncSession = Depends(get_db)
):
    messages = await ConversationService.get_conversation_messages(
        db_session, conversation_id
    )
    return {"messages": messages}


@app.get("/api/chat/conversations/{user_id}")
async def list_conversations(user_id: str, db_session: AsyncSession = Depends(get_db)):
    return await ConversationService.list_conversations(db_session, user_id)


@app.delete("/api/chat/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID, db_session: AsyncSession = Depends(get_db)
):
    success = await ConversationService.delete_conversation(db_session, conversation_id)
    await db_session.commit()
    return {"success": success}


@app.post("/api/chat/stream/rag")
async def stream_rag_chat(
    request: StreamingChatRequest, db_session: AsyncSession = Depends(get_db)
):
    """
    Stream chat responses with RAG integration using Server-Sent Events (SSE).
    This endpoint provides real-time feedback about document search and token-by-token response streaming.
    """
    return await rag_streaming_agent.create_streaming_response(request, db_session)


if __name__ == "__main__":
    logger.info("Starting Hermes API server")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
