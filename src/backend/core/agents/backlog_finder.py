import json
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from backend.core.utils.logger import log_and_stream
from backend.core.utils.message_type import MessageType


SYSTEM_PROMPT = """
You are an expert financial analyst. Your job is to answer how big a company's
backlog is based on the web pages provided.
"""


class BacklogResult(BaseModel):
    backlog_millions: int = Field(
        description="The company's backlog in millions of USD, "
                    "or 0 if unavailable."
    )


class BacklogFinder:
    def __init__(self) -> None:
        model = ChatOpenAI(
            model="gpt-6-luna",
            use_responses_api=True,
            reasoning_effort="medium"
        )

        self._agent = create_agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            response_format=ToolStrategy(BacklogResult)
        )
    
    async def run(self, company_name: str, prompt: dict) -> int:
        prompt = json.dumps(prompt, ensure_ascii=False)
        log_and_stream(
            "Running backlog finder agent",
            MessageType.info,
            prompt_size=len(prompt)
        )

        result = await self._agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": prompt
            }]
        })

        backlog = result["structured_response"].backlog_millions

        log_and_stream(
            f"{company_name}'s backlog is ${backlog} million",
            MessageType.info
        )
        
        return backlog
