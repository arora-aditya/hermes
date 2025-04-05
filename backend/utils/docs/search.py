from pydantic import BaseModel
import logging
from utils.vector_store import get_vector_store

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    query: str


class Search:
    def __init__(self):
        """Initialize the search service with PGVector."""
        try:
            logger.info("Initializing Search service")
            self.pgvector = get_vector_store()
            logger.info("Search service initialized successfully")
        except Exception as e:
            logger.error(
                f"Failed to initialize Search service: {str(e)}", exc_info=True
            )
            raise

    def search(self, query: str):
        """
        Perform similarity search using the vector store.

        Args:
            query: Search query string

        Returns:
            List of matching documents with similarity scores
        """
        try:
            logger.info(f"Performing similarity search with query: '{query}'")

            # Log the query embedding process
            logger.debug("Generating query embeddings")
            results = self.pgvector.similarity_search_with_score(query)

            # Convert results to documents with scores in metadata
            documents_with_scores = []
            for doc, score in results:
                doc.metadata["score"] = score
                documents_with_scores.append(doc)

            # Log search results details
            logger.info(f"Search completed. Found {len(documents_with_scores)} results")
            if documents_with_scores:
                logger.debug("Top results metadata:")
                for i, doc in enumerate(
                    documents_with_scores[:3]
                ):  # Log first 3 results
                    logger.debug(f"Result {i+1}:")
                    logger.debug(
                        f"  Document ID: {doc.metadata.get('document_id', 'N/A')}"
                    )
                    logger.debug(f"  Score: {doc.metadata.get('score', 'N/A')}")
                    logger.debug(f"  Page: {doc.metadata.get('page', 'N/A')}")
                    logger.debug(f"  Content preview: {doc.page_content[:100]}...")
            else:
                logger.warning("Search returned no results")

            return documents_with_scores
        except Exception as e:
            logger.error(f"Error during similarity search: {str(e)}", exc_info=True)
            raise
