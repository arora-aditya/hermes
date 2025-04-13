import logging
import os
import re
from typing import List, Optional

from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel
from utils.llm import get_openai_llm
from utils.vector_store import get_vector_store

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryOutputParser(BaseOutputParser[List[str]]):
    """Output parser that extracts clean search queries from formatted text."""

    def parse(self, text: str) -> List[str]:
        """
        Parse the text and extract only the actual search queries.

        Example input:
        1. # Basic keywords: CIBC Feb balance
        2. # Synonym variation: Canadian Imperial Bank of Commerce February statement
        3. # Technical terms: CIBC February financial report

        Returns:
        ['CIBC Feb balance',
         'Canadian Imperial Bank of Commerce February statement',
         'CIBC February financial report']
        """
        # Split into lines and remove empty lines
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]

        # Extract queries using regex pattern
        # Matches content after the format "number. # comment: "
        pattern = r"^\d+\.\s*#[^:]*:\s*(.+)$"

        queries = []
        for line in lines:
            match = re.match(pattern, line)
            if match:
                # Extract the actual query part
                query = match.group(1).strip()
                if query:  # Only add non-empty queries
                    queries.append(query)
            elif (
                line
            ):  # If line doesn't match pattern but isn't empty, include it as is
                queries.append(line)

        logger.debug(f"Parsed queries: {queries}")
        return queries


class Search:
    def __init__(self):
        """Initialize the search service with MultiQueryRetriever."""
        try:
            logger.info("Initializing Search service")
            self.vector_store = get_vector_store()
            self.llm = get_openai_llm(temperature=0)

            # Get prompt template from environment variables
            search_prompt = os.getenv("SEARCH_PROMPT")
            if not search_prompt:
                raise ValueError("SEARCH_PROMPT not found in environment variables")

            # Initialize custom prompt template for keyword refinement
            self.query_prompt = PromptTemplate(
                input_variables=["question"], template=search_prompt
            )

            # Initialize output parser
            self.output_parser = QueryOutputParser()

            # Create the LLM chain
            self.llm_chain = self.query_prompt | self.llm | self.output_parser

            logger.info("Search service initialized successfully")
        except Exception as e:
            logger.error(
                f"Failed to initialize Search service: {str(e)}", exc_info=True
            )
            raise

    def search(self, query: str, user_id: int, limit: Optional[int] = 5):
        """
        Search for documents using MultiQueryRetriever with user filtering.

        Args:
            query: Search query
            user_id: User ID to filter results
            limit: Maximum number of results to return per query

        Returns:
            List of relevant documents
        """
        try:
            logger.info(f"Starting search for query: '{query}' for user_id: {user_id}")

            # Create a filtered retriever
            base_retriever = self.vector_store.as_retriever(
                search_kwargs={
                    "k": limit,
                    "filter": {"user_id": user_id},  # Filter by user_id
                }
            )

            # Create MultiQueryRetriever with our custom prompt
            retriever = MultiQueryRetriever(
                retriever=base_retriever,
                llm_chain=self.llm_chain,
                parser_key="text",  # This matches the output of our parser
            )

            # Get unique documents across all generated queries
            logger.debug("Executing multi-query retrieval")
            docs = retriever.invoke(query)

            logger.info(f"Search complete. Found {len(docs)} relevant documents")
            return docs

        except Exception as e:
            logger.error(f"Error during document search: {str(e)}", exc_info=True)
            raise
