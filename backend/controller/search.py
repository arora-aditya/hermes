"""
Search Controller
===============
Handles document search operations including:
- Prefix/fuzzy search for documents
- Full-text search within documents
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from models.document import Document
from models.user_document import UserDocument
from schemas.document import DocumentPrefixSearchResponse, DocumentResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchRoutes:
    def __init__(self):
        self.router = APIRouter(prefix="/api/search", tags=["search"])
        self._setup_routes()

    def _setup_routes(self):
        self.router.add_api_route(
            "/prefix/{user_id}",
            self.prefix_search_documents,
            methods=["GET"],
            response_model=DocumentPrefixSearchResponse,
        )

    async def prefix_search_documents(
        self,
        user_id: int,
        query: str,
        similarity_threshold: float = 0.3,
        db: AsyncSession = Depends(get_db),
    ) -> DocumentPrefixSearchResponse:
        try:
            # Input validation
            if not query.strip():
                raise HTTPException(
                    status_code=422, detail="Search query cannot be empty"
                )

            logger.info(
                f"Starting prefix search for user_id={user_id}, query='{query}'"
            )

            # Calculate similarity score for reuse
            filename_similarity = func.similarity(Document.filename, query)

            # Build query with user access control
            query = (
                select(Document)
                .add_columns(filename_similarity.label("similarity_score"))
                .join(UserDocument)
                .where(
                    UserDocument.user_id == user_id,
                    Document.is_ingested == True,
                    or_(
                        # Search in filename using trigram similarity
                        filename_similarity > similarity_threshold,
                        # Search in path using LIKE
                        Document.path_ltree.like(f"%{query}%"),
                    ),
                )
                .order_by(
                    filename_similarity.desc()
                )  # Order directly by the similarity function
                .limit(10)  # Always return top 10 results
            )

            result = await db.execute(query)
            documents = result.unique().all()

            # Convert to response model
            document_responses = [
                DocumentResponse(
                    id=doc.Document.id,
                    filename=doc.Document.filename,
                    path_array=doc.Document.path_array,
                    is_ingested=doc.Document.is_ingested,
                    created_at=(
                        doc.Document.created_at.isoformat()
                        if doc.Document.created_at
                        else None
                    ),
                    updated_at=(
                        doc.Document.updated_at.isoformat()
                        if doc.Document.updated_at
                        else None
                    ),
                )
                for doc in documents
            ]

            return DocumentPrefixSearchResponse(documents=document_responses)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during prefix search: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error during prefix search: {str(e)}"
            )


# Initialize and export the router
search_routes = SearchRoutes()
router = search_routes.router
