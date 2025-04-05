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
            self.embeddings = OpenAIEmbeddings(
                api_key=os.environ["OPENAI_API_KEY"],
                model=os.environ.get(
                    "OPENAI_TEXT_EMBEDDING_MODEL", "text-embedding-3-small"
                ),
            )
            connection_string = os.environ["DATABASE_URL"]
            logger.info(f"Initializing PGVector with connection: {connection_string}")
            self.pgvector = PGVector(
                embeddings=self.embeddings,
                collection_name="my_docs",
                connection=connection_string,
                use_jsonb=True,
            )
            # Verify collection exists
            self.verify_collection()
        except Exception as e:
            logger.error(f"Error initializing Search: {str(e)}")
            raise

    def verify_collection(self):
        try:
            # Try a simple search to verify the collection exists and is accessible
            # This will raise an error if the collection doesn't exist
            results = self.pgvector.similarity_search_with_score("test query", k=1)
            logger.info(
                f"Collection verification successful. Found {len(results)} results."
            )
        except Exception as e:
            logger.error(f"Error verifying collection: {str(e)}")
            # Don't raise the error - if collection doesn't exist, it will be created when needed
            pass

    def search(self, query: str):
        try:
            logger.info(f"Performing search with query: {query}")
            results = self.pgvector.similarity_search(query)
            logger.info(f"Search returned {len(results)} results")
            if not results:
                logger.warning("Search returned no results")
            return results
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            raise
