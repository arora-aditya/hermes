from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
import os


class ChatRequest(BaseModel):
    message: str


class Agent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-exp"),
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=os.environ.get("GEMINI_API_KEY"),
        )
        self.messages = [
            {
                "role": "system",
                "content": os.getenv("GEMINI_SYSTEM_PROMPT"),
            }
        ]

    def chat(self, request: ChatRequest):
        self.messages.append({"role": "user", "content": request.message})
        response = self.llm.invoke(self.messages)
        self.messages.append({"role": "assistant", "content": response.content})
        return response.content
