from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from pydantic import BaseModel
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    query: str


class Search:
    def __init__(self):
        try:
            logger.info("Initializing Search service")
            self.embeddings = OpenAIEmbeddings(
                api_key=os.environ["OPENAI_API_KEY"],
                model=os.environ.get(
                    "OPENAI_TEXT_EMBEDDING_MODEL", "text-embedding-3-small"
                ),
            )
            logger.debug("OpenAI embeddings initialized")

            connection_string = os.environ["DATABASE_URL"]
            logger.info(f"Initializing PGVector with connection: {connection_string}")

            self.pgvector = PGVector(
                embeddings=self.embeddings,
                collection_name="my_docs",
                connection=connection_string,
                use_jsonb=True,
            )
            logger.debug("PGVector initialized successfully")

            # Verify collection exists
            self.verify_collection()
            logger.info("Search service initialization complete")
        except Exception as e:
            logger.error(f"Error initializing Search service: {str(e)}", exc_info=True)
            raise

    def verify_collection(self):
        try:
            # Try a simple search to verify the collection exists and is accessible
            logger.debug("Verifying collection existence and accessibility")
            results = self.pgvector.similarity_search_with_score("test query", k=1)
            logger.info(
                f"Collection verification successful. Found {len(results)} results."
            )

            # Log some details about the first result if available
            if results:
                result, score = results[0]
                logger.debug(f"Sample result metadata: {result.metadata}")
                logger.debug(f"Sample result score: {score}")
        except Exception as e:
            logger.warning(f"Collection verification failed: {str(e)}")
            logger.info("Collection will be created when documents are first embedded")

    def search(self, query: str):
        try:
            logger.info(f"Performing similarity search with query: '{query}'")

            # Log the query embedding process
            logger.debug("Generating query embeddings")
            results = self.pgvector.similarity_search(query)

            # Log search results details
            logger.info(f"Search completed. Found {len(results)} results")
            if results:
                logger.debug("Top results metadata:")
                for i, result in enumerate(results[:3]):  # Log first 3 results
                    logger.debug(f"Result {i+1}:")
                    logger.debug(
                        f"  Document ID: {result.metadata.get('document_id', 'N/A')}"
                    )
                    logger.debug(f"  Page: {result.metadata.get('page', 'N/A')}")
                    logger.debug(f"  Content preview: {result.page_content[:100]}...")
            else:
                logger.warning("Search returned no results")

            return results
        except Exception as e:
            logger.error(f"Error during similarity search: {str(e)}", exc_info=True)
            raise
