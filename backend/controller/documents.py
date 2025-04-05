from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from models.document import Document
from models.user_document import UserDocument
from utils.database import get_db
from utils.docs.chunk import Chunk
from utils.docs.embed import Embeddings
from utils.docs.search import Search
import os
import shutil
from langchain_community.document_loaders import PyPDFLoader
import logging

router = APIRouter(prefix="/api/documents", tags=["documents"])


# Pydantic models for request/response
class DocumentResponse(BaseModel):
    id: int
    filename: str
    is_ingested: bool
    created_at: str
    updated_at: Optional[str]


class SearchRequest(BaseModel):
    query: str
    user_id: int


class IngestRequest(BaseModel):
    document_ids: List[int] = Field(
        ..., description="List of document IDs to ingest", min_items=1
    )


# Initialize required services
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
chunk_service = Chunk()
embeddings_service = Embeddings()
search_service = Search()


@router.post("/upload", response_model=List[DocumentResponse])
async def upload_documents(
    user_id: int,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        saved_files = []
        for file in files:
            # Save file to disk
            file_path = UPLOAD_DIR / file.filename
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Create document record
            doc = Document(
                filename=file.filename,
                file_path=str(file_path.absolute()),
                is_ingested=False,
            )
            db.add(doc)
            await db.commit()
            await db.refresh(doc)

            # Create user-document mapping
            user_doc = UserDocument(user_id=user_id, document_id=doc.id)
            db.add(user_doc)
            await db.commit()

            saved_files.append(
                DocumentResponse.model_validate(
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "is_ingested": doc.is_ingested,
                        "created_at": (
                            doc.created_at.isoformat() if doc.created_at else None
                        ),
                        "updated_at": (
                            doc.updated_at.isoformat() if doc.updated_at else None
                        ),
                    }
                )
            )

        return saved_files

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=List[DocumentResponse])
async def list_documents(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # Query documents through user_documents relationship
        query = (
            select(Document)
            .distinct()
            .join(UserDocument)
            .where(UserDocument.user_id == user_id)
        )
        result = await db.execute(query)
        documents = result.unique().scalars().all()

        # Convert SQLAlchemy models to dictionaries before Pydantic validation
        return [
            DocumentResponse.model_validate(
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "is_ingested": doc.is_ingested,
                    "created_at": (
                        doc.created_at.isoformat() if doc.created_at else None
                    ),
                    "updated_at": (
                        doc.updated_at.isoformat() if doc.updated_at else None
                    ),
                }
            )
            for doc in documents
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{document_id}")
async def update_document(
    document_id: int,
    user_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Verify document exists and belongs to user
        query = (
            select(Document)
            .join(UserDocument)
            .where(Document.id == document_id)
            .where(UserDocument.user_id == user_id)
        )
        result = await db.execute(query)
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete old file
        old_file_path = Path(document.file_path)
        if old_file_path.exists():
            old_file_path.unlink()

        # Save new file
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Update document record
        document.filename = file.filename
        document.file_path = str(file_path.absolute())
        document.is_ingested = False
        await db.commit()
        await db.refresh(document)

        return DocumentResponse.model_validate(
            {
                "id": document.id,
                "filename": document.filename,
                "is_ingested": document.is_ingested,
                "created_at": (
                    document.created_at.isoformat() if document.created_at else None
                ),
                "updated_at": (
                    document.updated_at.isoformat() if document.updated_at else None
                ),
            }
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    document_id: int, user_id: int, db: AsyncSession = Depends(get_db)
):
    try:
        # Verify document exists and belongs to user
        query = (
            select(Document)
            .distinct()
            .join(UserDocument)
            .where(Document.id == document_id)
            .where(UserDocument.user_id == user_id)
        )
        result = await db.execute(query)
        document = result.unique().scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete file from filesystem
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()

        # Delete document and user_document records
        await db.execute(
            delete(UserDocument).where(UserDocument.document_id == document_id)
        )
        await db.execute(delete(Document).where(Document.id == document_id))
        await db.commit()

        return {"message": "Document deleted successfully"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def ingest_documents(
    request: IngestRequest, user_id: int, db: AsyncSession = Depends(get_db)
):
    try:
        all_docs = []

        # Verify all documents exist and belong to user
        for doc_id in request.document_ids:
            query = (
                select(Document)
                .distinct()
                .join(UserDocument)
                .where(Document.id == doc_id)
                .where(UserDocument.user_id == user_id)
            )
            result = await db.execute(query)
            document = result.unique().scalar_one_or_none()

            if not document:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document with id {doc_id} not found or not accessible",
                )
            all_docs.append(document)

        # Process all documents
        processed_docs = []
        for document in all_docs:
            try:
                loader = PyPDFLoader(document.file_path)
                pages = loader.load()
                # Add document_id to each page's metadata as an integer
                for page in pages:
                    page.metadata["document_id"] = (
                        document.id
                    )  # Store as integer, not string
                processed_docs.extend(pages)

                # Update document status
                document.is_ingested = True
                await db.commit()
            except Exception as e:
                # Log specific document processing error but continue with others
                logging.error(f"Error processing document {document.id}: {str(e)}")
                continue

        if not processed_docs:
            raise HTTPException(
                status_code=422, detail="No documents could be processed successfully"
            )

        # Process documents through chunking and embedding pipeline
        chunks = chunk_service.chunk_docs(processed_docs)
        embeddings = embeddings_service.embed_docs(chunks)

        return {
            "message": "Documents ingested successfully",
            "document_ids": request.document_ids,
            "chunks_created": len(chunks),
            "embeddings_created": (
                len(embeddings) if isinstance(embeddings, list) else 1
            ),
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        print(e)
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error during document ingestion: {str(e)}"
        )


@router.post("/search")
async def search_documents(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Input validation
        if not request.query.strip():
            raise HTTPException(status_code=422, detail="Search query cannot be empty")

        # Log search request
        logging.info(
            f"Search request received - query: {request.query}, user_id: {request.user_id}"
        )

        # First verify if user has any documents
        user_docs_query = (
            select(Document.id)
            .join(UserDocument)
            .where(UserDocument.user_id == request.user_id)
        )
        result = await db.execute(user_docs_query)
        user_doc_ids = [r[0] for r in result.all()]

        if not user_doc_ids:
            logging.warning(f"User {request.user_id} has no documents")
            return {
                "documents": [],
                "total": 0,
                "message": "No documents found for this user",
            }

        logging.info(f"User {request.user_id} has documents: {user_doc_ids}")

        # Perform similarity search
        try:
            search_results = search_service.search(request.query)
            logging.info(
                f"Search returned {len(search_results) if search_results else 0} results"
            )
        except Exception as e:
            logging.error(f"Error performing similarity search: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error performing similarity search: {str(e)}"
            )

        # Extract document IDs from search results and ensure they are integers
        document_ids = []
        for result in search_results:
            if result.metadata and "document_id" in result.metadata:
                doc_id = result.metadata["document_id"]
                # Convert to int if it's not already
                if isinstance(doc_id, str):
                    try:
                        doc_id = int(doc_id)
                    except ValueError:
                        logging.warning(f"Invalid document_id in metadata: {doc_id}")
                        continue
                document_ids.append(doc_id)

        logging.info(f"Found document IDs in search results: {document_ids}")

        if not document_ids:
            logging.warning("No document IDs found in search results")
            return {
                "documents": [],
                "total": 0,
                "message": "No matching documents found",
            }

        # Filter results to only include documents the user has access to
        query = (
            select(Document)
            .distinct()
            .join(UserDocument)
            .where(Document.id.in_(document_ids))
            .where(UserDocument.user_id == request.user_id)
        )
        result = await db.execute(query)
        accessible_documents = result.unique().scalars().all()

        logging.info(f"Found {len(accessible_documents)} accessible documents for user")

        return {
            "documents": [
                DocumentResponse.model_validate(
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "is_ingested": doc.is_ingested,
                        "created_at": (
                            doc.created_at.isoformat() if doc.created_at else None
                        ),
                        "updated_at": (
                            doc.updated_at.isoformat() if doc.updated_at else None
                        ),
                    }
                )
                for doc in accessible_documents
            ],
            "total": len(accessible_documents),
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error during document search: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error during document search: {str(e)}"
        )
