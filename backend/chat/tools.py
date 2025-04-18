import logging
from typing import Callable, List, Optional

from controller.documents import document_routes
from langchain_core.documents import Document as LangchainDocument
from langchain_core.tools import tool
from schemas.document import SearchRequest
from sqlalchemy.ext.asyncio import AsyncSession
from utils.docs.search import Search

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_search_documents_tool(user_id: str, db: AsyncSession) -> Callable:
    """Creates a search documents tool for a specific user.

    Args:
        user_id: The ID of the user for whom to create the search tool.

    Returns:
        A tool-annotated function that can search documents for the specified user.
    """

    @tool
    async def search_documents_for_user(query: str) -> str:
        """Search for documents in the database for a specific user.

        Args:
            query: The query to search for.

        Returns:
            A string containing the search results, and the content of the documents, that can be used to answer the question.
        """
        try:
            # Use the existing search endpoint
            search_request = SearchRequest(
                query=query,
                user_id=user_id,
                chunks_per_document=10,  # Limit to top 3 chunks per document
                min_score=0.3,  # Only use chunks with good relevance
                sort_by_score=True,
            )

            search_response = await document_routes.search_documents(search_request, db)

            if search_response.get("documents"):
                context_chunks = []
                for doc in search_response["documents"]:
                    for chunk in doc.chunks:
                        context_chunks.append(
                            f"Document {doc.filename}, Page {chunk.page_number or 'unknown'}: {chunk.content}"
                        )
                logger.info(
                    f"Added {len(context_chunks)} relevant document chunks as context"
                )
                return "\n\n".join(context_chunks)
            return "No relevant documents found."

        except Exception as e:
            logger.error(f"Error during document search: {str(e)}", exc_info=True)
            return f"Error searching documents: {str(e)}"

    return search_documents_for_user


def create_streaming_search_tool(user_id: str, db: AsyncSession) -> Callable:
    """Creates a streaming search documents tool that returns document objects directly.

    Args:
        user_id: The ID of the user for whom to create the search tool.
        db: The database session.

    Returns:
        A tool-annotated function that can search documents and return Langchain Document objects.
    """

    @tool
    async def search_documents_streaming(query: str) -> List[LangchainDocument]:
        """Search for documents in the database for a specific user.

        Args:
            query: The query to search for.

        Returns:
            A list of Langchain Document objects containing the search results.
        """
        try:
            # Use the existing search endpoint with same parameters as non-streaming search
            search_request = SearchRequest(
                query=query,
                user_id=user_id,
                chunks_per_document=10,  # Limit to top 10 chunks per document
                min_score=0.3,  # Only use chunks with good relevance
                sort_by_score=True,
            )

            search_response = await document_routes.search_documents(search_request, db)

            if not search_response.get("documents"):
                return []

            # Convert the response documents to Langchain Document objects
            langchain_docs = []
            for doc in search_response["documents"]:
                for chunk in doc.chunks:
                    langchain_docs.append(
                        LangchainDocument(
                            page_content=chunk.content,
                            metadata={
                                "document_id": doc.id,
                                "filename": doc.filename,
                                "score": chunk.score,
                                "page": chunk.page_number,
                                "chunk_index": chunk.chunk_index,
                            },
                        )
                    )

            return langchain_docs

        except Exception as e:
            logger.error(
                f"Error during streaming document search: {str(e)}", exc_info=True
            )
            raise Exception(f"Error searching documents: {str(e)}")

    return search_documents_streaming
