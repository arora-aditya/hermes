from load_env import IS_ENV_LOADED
from fastapi import FastAPI, Depends, File, UploadFile
from chat.agent import ChatRequest
from chat.agent import Agent
from chat.conversation import ConversationService
from document.ingest import IngestRequest
from document.search import SearchRequest
from document.app import App
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from document.database import Database
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from uuid import UUID
from controller import users, organizations
from document.database import get_db
from models.relationships import setup_relationships


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not IS_ENV_LOADED:
        raise Exception("Environment variables not loaded")

    # Set up SQLAlchemy relationships
    setup_relationships()

    yield
    # Shutdown
    pass


app = FastAPI(lifespan=lifespan)
document = App()
agent = Agent()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(users.router, prefix="/api")
app.include_router(organizations.router, prefix="/api")


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/api/ingest")
async def ingest(request: IngestRequest, db_session: AsyncSession = Depends(get_db)):
    return await document.digest(request, db_session)


@app.post("/api/search")
def search(request: SearchRequest):
    return document.search_files(request)


@app.post("/api/uploadfiles/{user_id}")
async def upload_files(
    user_id: str,
    files: List[UploadFile] = [File(...)],
    db_session: AsyncSession = Depends(get_db),
):
    return await document.upload_local(user_id, files, db_session)


@app.get("/api/listfiles")
async def list_files(db_session: AsyncSession = Depends(get_db)):
    return await document.list_files(db_session)


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


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
