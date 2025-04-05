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

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


# Pydantic models for request/response
class DocumentResponse(BaseModel):
    id: int
    filename: str
    is_ingested: bool
    created_at: str
    updated_at: Optional[str]


class ChunkResponse(BaseModel):
    content: str
    score: float
    page_number: Optional[int]
    chunk_index: Optional[int]


class DocumentWithChunksResponse(DocumentResponse):
    chunks: List[ChunkResponse] = []


class SearchRequest(BaseModel):
    query: str
    user_id: int
    chunks_per_document: Optional[int] = 50
    min_score: Optional[float] = 0.7
    sort_by_score: Optional[bool] = True


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
        logger.info(
            f"Starting document upload for user_id={user_id}, files={[f.filename for f in files]}"
        )
        saved_files = []
        for file in files:
            logger.debug(f"Processing file: {file.filename}")
            # Save file to disk
            file_path = UPLOAD_DIR / file.filename
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logger.debug(f"File saved to disk: {file_path}")

            # Create document record
            doc = Document(
                filename=file.filename,
                file_path=str(file_path.absolute()),
                is_ingested=False,
            )
            db.add(doc)
            await db.commit()
            await db.refresh(doc)
            logger.debug(f"Document record created: id={doc.id}")

            # Create user-document mapping
            user_doc = UserDocument(user_id=user_id, document_id=doc.id)
            db.add(user_doc)
            await db.commit()
            logger.debug(
                f"User-document mapping created: user_id={user_id}, document_id={doc.id}"
            )

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

        logger.info(
            f"Successfully uploaded {len(saved_files)} files for user_id={user_id}"
        )
        return saved_files

    except Exception as e:
        logger.error(
            f"Error during document upload for user_id={user_id}: {str(e)}",
            exc_info=True,
        )
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
        logger.info(
            f"Starting document ingestion for user_id={user_id}, document_ids={request.document_ids}"
        )
        all_docs = []

        # Verify all documents exist and belong to user
        for doc_id in request.document_ids:
            logger.debug(
                f"Verifying document access: doc_id={doc_id}, user_id={user_id}"
            )
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
                logger.warning(
                    f"Document not found or not accessible: doc_id={doc_id}, user_id={user_id}"
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"Document with id {doc_id} not found or not accessible",
                )
            all_docs.append(document)
            logger.debug(f"Document verified: doc_id={doc_id}")

        # Process all documents
        processed_docs = []
        for document in all_docs:
            try:
                logger.debug(
                    f"Processing document: id={document.id}, filename={document.filename}"
                )
                loader = PyPDFLoader(document.file_path)
                pages = loader.load()
                logger.debug(f"Document loaded: id={document.id}, pages={len(pages)}")

                # Add document_id to each page's metadata
                for page in pages:
                    page.metadata["document_id"] = document.id
                    logger.debug(
                        f"Added metadata to page: doc_id={document.id}, page_number={page.metadata.get('page', 'unknown')}"
                    )
                processed_docs.extend(pages)

                # Update document status
                document.is_ingested = True
                await db.commit()
                logger.debug(f"Document marked as ingested: id={document.id}")
            except Exception as e:
                logger.error(
                    f"Error processing document {document.id}: {str(e)}", exc_info=True
                )
                continue

        if not processed_docs:
            logger.error("No documents could be processed successfully")
            raise HTTPException(
                status_code=422, detail="No documents could be processed successfully"
            )

        # Process documents through chunking and embedding pipeline
        logger.info(f"Starting chunking process for {len(processed_docs)} pages")
        chunks = chunk_service.chunk_docs(processed_docs)
        logger.info(f"Chunking complete. Created {len(chunks)} chunks")

        logger.info("Starting embedding process")
        embeddings = embeddings_service.embed_docs(chunks)
        logger.info(
            f"Embedding complete. Created {len(embeddings) if isinstance(embeddings, list) else 1} embeddings"
        )

        return {
            "message": "Documents ingested successfully",
            "document_ids": request.document_ids,
            "chunks_created": len(chunks),
            "embeddings_created": (
                len(embeddings) if isinstance(embeddings, list) else 1
            ),
        }

    except HTTPException:
        logger.error("HTTP exception during ingestion", exc_info=True)
        await db.rollback()
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during document ingestion: {str(e)}", exc_info=True
        )
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error during document ingestion: {str(e)}"
        )


@router.post("/search")
async def search_documents(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Input validation
        if not request.query.strip():
            logger.warning(
                f"Empty search query received from user_id={request.user_id}"
            )
            raise HTTPException(status_code=422, detail="Search query cannot be empty")

        logger.info(
            f"Search request received - query='{request.query}', user_id={request.user_id}"
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
            logger.warning(f"User {request.user_id} has no documents")
            return {
                "documents": [],
                "total": 0,
                "message": "No documents found for this user",
            }

        logger.debug(f"User {request.user_id} has access to documents: {user_doc_ids}")

        # Perform similarity search
        try:
            logger.debug(f"Performing similarity search with query: '{request.query}'")
            search_results = search_service.search(request.query)
            logger.info(
                f"Search returned {len(search_results) if search_results else 0} results"
            )
        except Exception as e:
            logger.error(f"Error performing similarity search: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Error performing similarity search: {str(e)}"
            )

        # Group results by document and filter by score
        document_chunks = {}
        all_chunks = []  # Store all chunks for global sorting
        for result in search_results:
            if not result.metadata or "document_id" not in result.metadata:
                continue

            score = result.metadata.get("score", 0)
            if score < request.min_score:
                continue

            doc_id = result.metadata["document_id"]
            if isinstance(doc_id, str):
                try:
                    doc_id = int(doc_id)
                except ValueError:
                    continue

            if doc_id not in document_chunks:
                document_chunks[doc_id] = []

            chunk_response = ChunkResponse(
                content=result.page_content,
                score=score,
                page_number=result.metadata.get("page"),
                chunk_index=result.metadata.get("chunk_index"),
            )

            document_chunks[doc_id].append(chunk_response)
            all_chunks.append((doc_id, chunk_response))

        # Sort all chunks by score if requested
        if request.sort_by_score:
            all_chunks.sort(key=lambda x: x[1].score, reverse=True)

            # Rebuild document_chunks with sorted chunks
            document_chunks = {}
            for doc_id, chunk in all_chunks:
                if doc_id not in document_chunks:
                    document_chunks[doc_id] = []
                if len(document_chunks[doc_id]) < request.chunks_per_document:
                    document_chunks[doc_id].append(chunk)
        else:
            # Sort chunks within each document and apply limit
            for doc_id in document_chunks:
                if request.sort_by_score:
                    # Sort by score within document
                    document_chunks[doc_id].sort(key=lambda x: x.score, reverse=True)
                else:
                    # Sort by page number and chunk index to maintain document flow
                    document_chunks[doc_id].sort(
                        key=lambda x: (x.page_number or 0, x.chunk_index or 0)
                    )
                if request.chunks_per_document:
                    document_chunks[doc_id] = document_chunks[doc_id][
                        : request.chunks_per_document
                    ]

        # Get document metadata for documents with matching chunks
        document_ids = list(document_chunks.keys())
        if not document_ids:
            return {
                "documents": [],
                "total": 0,
                "message": "No matching chunks found above score threshold",
            }

        query = (
            select(Document)
            .distinct()
            .join(UserDocument)
            .where(Document.id.in_(document_ids))
            .where(UserDocument.user_id == request.user_id)
        )
        result = await db.execute(query)
        accessible_documents = result.unique().scalars().all()

        # Prepare response with documents and their chunks
        response_documents = []
        for doc in accessible_documents:
            doc_response = DocumentWithChunksResponse(
                id=doc.id,
                filename=doc.filename,
                is_ingested=doc.is_ingested,
                created_at=doc.created_at.isoformat() if doc.created_at else None,
                updated_at=doc.updated_at.isoformat() if doc.updated_at else None,
                chunks=document_chunks.get(doc.id, []),
            )
            response_documents.append(doc_response)

        # Sort documents by their highest scoring chunk
        if request.sort_by_score:
            response_documents.sort(
                key=lambda x: max((c.score for c in x.chunks), default=0), reverse=True
            )

        return {
            "documents": response_documents,
            "total": len(response_documents),
            "total_chunks": sum(len(doc.chunks) for doc in response_documents),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during document search: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Error during document search: {str(e)}"
        )
