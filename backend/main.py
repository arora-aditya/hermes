from fastapi import FastAPI, Depends
from fastapi import UploadFile
from fastapi import File
from chat.agent import ChatRequest
from chat.agent import ConversationRequest
from chat.agent import Agent
from document.ingest import IngestRequest
from document.search import SearchRequest
from document.app import App
import uvicorn
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from document.database import Database
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

load_dotenv()

db = Database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Shutdown
    pass


app = FastAPI(lifespan=lifespan)
document = App()
agent = Agent()


# Make the database session available as a dependency
async def get_db():
    async for session in db.get_session():
        yield session


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/api/ingest")
async def ingest(request: IngestRequest, db_session: AsyncSession = Depends(get_db)):
    return await document.digest(request, db_session)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/search")
def search(request: SearchRequest):
    return document.search_files(request)


@app.post("/api/uploadfiles")
async def upload_files(
    files: List[UploadFile] = [File(...)], db_session: AsyncSession = Depends(get_db)
):
    return await document.upload_local(files, db_session)


@app.get("/api/listfiles")
async def list_files(db_session: AsyncSession = Depends(get_db)):
    return await document.list_files(db_session)


@app.post("/api/chat")
async def chat(request: ChatRequest, db_session: AsyncSession = Depends(get_db)):
    return await agent.chat(request, db_session)


@app.get("/api/chat/conversation/{conversation_id}")
async def chat(conversation_id: str, db_session: AsyncSession = Depends(get_db)):
    conversation = await agent.get_conversation_messages(
        db_session, ConversationRequest(conversation_id=conversation_id)
    )
    return {"messages": conversation}


@app.get("/api/chat/conversations/{user_id}")
async def chat(user_id: str, db_session: AsyncSession = Depends(get_db)):
    conversations = await agent.get_conversations(db_session, user_id)
    return conversations


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
