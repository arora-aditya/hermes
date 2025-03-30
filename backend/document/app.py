from document.ingest import Ingest
from document.chunk import Chunk
from document.embed import Embeddings
from document.upload import Upload
from document.ingest import IngestRequest
from document.search import Search, SearchRequest
from fastapi import UploadFile, File
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession


class App:
    def __init__(self):
        self.ingest = Ingest()
        self.chunk = Chunk()
        self.embeddings = Embeddings()
        self.upload = Upload()
        self.search = Search()

    async def upload_local(self, files: List[UploadFile], db: AsyncSession):
        return await self.upload.local_upload(db, files)

    async def list_files(self, db: AsyncSession):
        return await self.upload.list_files(db)

    def search_files(self, query: SearchRequest):
        return self.search.search(query)

    async def digest(self, request: IngestRequest, db: AsyncSession):
        docs = await self.ingest.ingest_docs(request.document_ids, db)
        chunks = self.chunk.chunk_docs(docs)
        embeddings = self.embeddings.embed_docs(chunks)
        return {
            "message": "docs ingested",
            "embeddings": embeddings,
        }
