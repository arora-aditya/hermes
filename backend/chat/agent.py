from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, UUID4
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.conversation import Message, ConversationHistory
from uuid import UUID
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage
from chat.conversation import ConversationService
from chat.conversation import ChatRequest, ChatResponse
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from chat.tools import create_search_documents_tool
from langchain.prompts import ChatPromptTemplate


class Agent:
    def __init__(self):
        if os.environ.get("USE_REAL_LLM", "true") == "true":
            self.llm = ChatGoogleGenerativeAI(
                model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-exp"),
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                api_key=os.environ.get("GEMINI_API_KEY"),
            )
        else:
            self.llm = FakeListChatModel(
                responses=["This is a test response from the fake chat model."]
            )

        self.system_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", os.getenv("GEMINI_SYSTEM_PROMPT")),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

    async def chat(self, request: ChatRequest, db: AsyncSession):
        # Create the search documents tool for this specific user
        search_tool = create_search_documents_tool(user_id=request.user_id, db=db)

        # Create an agent with the search tool
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=[search_tool],
            prompt=self.system_prompt,
        )

        # Create the agent executor
        agent_executor = AgentExecutor(agent=agent, tools=[search_tool], verbose=True)

        # Get messages prepared for LLM
        messages = await ConversationService.prepare_messages_for_llm(
            db, request, self.system_prompt
        )

        # Execute the agent with the user's message
        result = await agent_executor.ainvoke(
            {
                "input": request.message,
                "chat_history": messages[
                    1:-1
                ],  # Exclude system prompt and current message
            },
            config={
                "metadata": {
                    "session_id": (
                        str(request.conversation_id)
                        if request.conversation_id
                        else None
                    )
                }
            },
        )

        # Process the complete chat interaction
        conversation = await ConversationService.process_chat_interaction(
            db=db,
            user_id=request.user_id,
            message=request.message,
            conversation_id=request.conversation_id,
            system_prompt=self.system_prompt,
            llm_response=result["output"],
        )

        return ChatResponse(
            message=result["output"], conversation_id=conversation.conversation_id
        )
