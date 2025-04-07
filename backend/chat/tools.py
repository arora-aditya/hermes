from typing import Optional, Callable
from langchain_core.tools import tool
from controller.documents import search_documents, SearchRequest
from sqlalchemy.ext.asyncio import AsyncSession
import logging

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

            search_response = await search_documents(search_request, db)

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
