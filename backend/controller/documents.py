import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from langchain_community.document_loaders import PyPDFLoader
from models.document import Document
from models.user_document import UserDocument
from schemas.document import (
    ChunkResponse,
    DirectoryTreeResponse,
    DocumentResponse,
    DocumentWithChunksResponse,
    IngestRequest,
    SearchRequest,
)
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database import get_db
from utils.docs.chunk import Chunk
from utils.docs.directory import build_directory_tree
from utils.docs.embed import Embeddings
from utils.docs.search import Search

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DocumentRoutes:
    def __init__(self):
        self.router = APIRouter(prefix="/api/documents", tags=["documents"])
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        self.chunk_service = Chunk()
        self.embeddings_service = Embeddings()
        self.search_service = Search()
        self._setup_routes()

    def _setup_routes(self):
        self.router.add_api_route(
            "/upload",
            self.upload_documents,
            methods=["POST"],
            response_model=List[DocumentResponse],
        )
        self.router.add_api_route(
            "/{user_id}",
            self.list_documents,
            methods=["GET"],
            response_model=DirectoryTreeResponse,
        )
        self.router.add_api_route(
            "/{document_id}", self.update_document, methods=["PUT"]
        )
        self.router.add_api_route(
            "/{document_id}", self.delete_document, methods=["DELETE"]
        )
        self.router.add_api_route("/ingest", self.ingest_documents, methods=["POST"])
        self.router.add_api_route("/search", self.search_documents, methods=["POST"])

    async def upload_documents(
        self,
        user_id: int,
        files: List[UploadFile] = File(...),
        path: Optional[str] = Query(
            None, description="Target directory path (e.g., 'projects/2024')"
        ),
        db: AsyncSession = Depends(get_db),
    ):
        try:
            logger.info(
                f"Starting document upload for user_id={user_id}, files={[f.filename for f in files]}, path={path}"
            )

            # Convert path string to array if provided
            path_array = path.split("/") if path else []

            saved_files = []
            for file in files:
                logger.debug(f"Processing file: {file.filename}")

                # Create full path array including filename
                full_path_array = path_array + [file.filename]

                # Create directory structure if needed
                if path_array:
                    dir_path = self.upload_dir.joinpath(*path_array)
                    dir_path.mkdir(parents=True, exist_ok=True)
                    file_path = dir_path / file.filename
                else:
                    file_path = self.upload_dir / file.filename

                # Save file to disk
                with file_path.open("wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                logger.debug(f"File saved to disk: {file_path}")

                # Create document record
                doc = Document(
                    filename=file.filename,
                    path_array=full_path_array,
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

    async def list_documents(
        self,
        user_id: int,
        path: Optional[str] = Query(None, description="Filter by directory path"),
        recursive: bool = Query(True, description="Include subdirectories"),
        db: AsyncSession = Depends(get_db),
    ):
        try:
            # Convert path string to array if provided
            path_array = path.split("/") if path else None

            # Query documents through user_documents relationship
            query = (
                select(Document)
                .distinct()
                .join(UserDocument)
                .where(UserDocument.user_id == user_id)
            )

            # Add path filter if provided and not recursive
            if path_array and not recursive:
                query = query.where(Document.path_array == path_array)

            result = await db.execute(query)
            documents = result.unique().scalars().all()

            # Build directory tree
            tree_children = build_directory_tree(
                documents, path_array if not recursive else None
            )

            return DirectoryTreeResponse(children=tree_children)

        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def update_document(
        self,
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
            file_path = self.upload_dir / file.filename
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

    async def delete_document(
        self, document_id: int, user_id: int, db: AsyncSession = Depends(get_db)
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

    async def ingest_documents(
        self, request: IngestRequest, user_id: int, db: AsyncSession = Depends(get_db)
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
                    logger.debug(
                        f"Document loaded: id={document.id}, pages={len(pages)}"
                    )

                    # Add document_id to each page's metadata
                    for page in pages:
                        page.metadata["document_id"] = document.id
                        page.metadata["user_id"] = user_id  # Add user_id to metadata
                        logger.debug(
                            f"Added metadata to page: doc_id={document.id}, user_id={user_id}, page_number={page.metadata.get('page', 'unknown')}"
                        )
                    processed_docs.extend(pages)

                    # Update document status
                    document.is_ingested = True
                    await db.commit()
                    logger.debug(f"Document marked as ingested: id={document.id}")
                except Exception as e:
                    logger.error(
                        f"Error processing document {document.id}: {str(e)}",
                        exc_info=True,
                    )
                    continue

            if not processed_docs:
                logger.error("No documents could be processed successfully")
                raise HTTPException(
                    status_code=422,
                    detail="No documents could be processed successfully",
                )

            # Process documents through chunking and embedding pipeline
            logger.info(f"Starting chunking process for {len(processed_docs)} pages")
            chunks = self.chunk_service.chunk_docs(processed_docs)
            logger.info(f"Chunking complete. Created {len(chunks)} chunks")

            logger.info("Starting embedding process")
            embeddings = self.embeddings_service.embed_docs(chunks)
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

    async def search_documents(
        self, request: SearchRequest, db: AsyncSession = Depends(get_db)
    ):
        try:
            # Input validation
            if not request.query.strip():
                logger.warning(
                    f"Empty search query received from user_id={request.user_id}"
                )
                raise HTTPException(
                    status_code=422, detail="Search query cannot be empty"
                )

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

            logger.debug(
                f"User {request.user_id} has access to documents: {user_doc_ids}"
            )

            # Perform multi-query search with user filtering
            try:
                logger.debug(
                    f"Performing multi-query search with query: '{request.query}'"
                )
                search_results = self.search_service.search(
                    query=request.query,
                    user_id=request.user_id,
                    limit=request.chunks_per_document,
                )
                logger.info(
                    f"Search returned {len(search_results) if search_results else 0} results"
                )
            except Exception as e:
                logger.error(f"Error performing search: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500, detail=f"Error performing search: {str(e)}"
                )

            # Group results by document
            document_chunks = {}
            for doc in search_results:
                if not doc.metadata or "document_id" not in doc.metadata:
                    continue

                doc_id = doc.metadata["document_id"]
                if isinstance(doc_id, str):
                    try:
                        doc_id = int(doc_id)
                    except ValueError:
                        continue

                if doc_id not in document_chunks:
                    document_chunks[doc_id] = []

                # Create chunk response
                chunk_response = ChunkResponse(
                    content=doc.page_content,
                    score=doc.metadata.get("score", 0.0),
                    page_number=doc.metadata.get("page"),
                    chunk_index=doc.metadata.get("chunk_index"),
                )
                document_chunks[doc_id].append(chunk_response)

            # Get document metadata for documents with matching chunks
            document_ids = list(document_chunks.keys())
            if not document_ids:
                return {
                    "documents": [],
                    "total": 0,
                    "message": "No matching documents found",
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
                    path_array=doc.path_array,
                    is_ingested=doc.is_ingested,
                    created_at=doc.created_at.isoformat() if doc.created_at else None,
                    updated_at=doc.updated_at.isoformat() if doc.updated_at else None,
                    chunks=document_chunks.get(doc.id, []),
                )
                response_documents.append(doc_response)

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


# Initialize and export the router
document_routes = DocumentRoutes()
router = document_routes.router
