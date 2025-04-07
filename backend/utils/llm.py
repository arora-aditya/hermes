from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.fake_chat_models import FakeListChatModel
import os
import logging

logger = logging.getLogger(__name__)


def get_openai_llm(temperature: float = 0) -> ChatOpenAI:
    """
    Get an instance of OpenAI's ChatGPT model.
    If USE_REAL_LLM is false, returns a fake chat model for testing.

    Args:
        temperature: The temperature for the model's output (0 = deterministic, 1 = creative)

    Returns:
        ChatOpenAI instance or FakeListChatModel for testing
    """
    try:
        if os.environ.get("USE_REAL_LLM", "true") == "true":
            return ChatOpenAI(temperature=temperature)
        else:
            return FakeListChatModel(
                responses=["This is a test response from the fake chat model."]
            )
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI LLM: {str(e)}", exc_info=True)
        raise


def get_gemini_llm() -> ChatGoogleGenerativeAI:
    """
    Get an instance of Google's Gemini model based on environment configuration.
    If USE_REAL_LLM is false, returns a fake chat model for testing.

    Returns:
        ChatGoogleGenerativeAI instance or FakeListChatModel for testing
    """
    try:
        if os.environ.get("USE_REAL_LLM", "true") == "true":
            return ChatGoogleGenerativeAI(
                model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-exp"),
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                api_key=os.environ.get("GEMINI_API_KEY"),
            )
        else:
            return FakeListChatModel(
                responses=["This is a test response from the fake chat model."]
            )
    except Exception as e:
        logger.error(f"Failed to initialize Gemini LLM: {str(e)}", exc_info=True)
        raise
