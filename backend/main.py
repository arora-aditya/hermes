from fastapi import FastAPI
from fastapi import UploadFile
from fastapi import File
from document.ingest import IngestRequest
from document.search import SearchRequest
from document.app import App
import uvicorn
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from typing import List

load_dotenv()
app = FastAPI()
document = App()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/api/ingest")
def ingest(request: IngestRequest):
    return document.digest(request)


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
async def upload_files(files: List[UploadFile] = File(...)):
    return await document.upload_local(files)


@app.get("/api/listfiles")
async def list_files():
    return document.list_files()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
