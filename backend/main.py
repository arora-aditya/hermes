from fastapi import FastAPI, Depends
from fastapi import UploadFile
from fastapi import File
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
    # Startup
    await db.init_db()
    yield
    # Shutdown
    pass


app = FastAPI(lifespan=lifespan)
document = App()


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
    files: List[UploadFile] = File(...), db_session: AsyncSession = Depends(get_db)
):
    return await document.upload_local(files, db_session)


@app.get("/api/listfiles")
async def list_files(db_session: AsyncSession = Depends(get_db)):
    return await document.list_files(db_session)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
