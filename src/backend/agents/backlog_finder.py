import json
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel, Field
import structlog


SYSTEM_PROMPT = """
You are an expert financial analyst. Your job is to answer how big a company's backlog is based on the web pages provided.
"""


_logger = structlog.get_logger(__name__)


class BacklogResult(BaseModel):
    backlog_millions: int = Field(
        description="The company's backlog in millions of USD, or 0 if unavailable."
    )


class BacklogFinder:
    def __init__(self):
        self._provider = "openai"
        self._model = "gpt-5.4-nano"
        
        self._agent = create_agent(
            model=f"{self._provider}:{self._model}",
            system_prompt=SYSTEM_PROMPT,
            response_format=ToolStrategy(BacklogResult)
        )
    
    async def run(self, company_name: str, prompt: dict) -> int:
        result = await self._agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": json.dumps(prompt, ensure_ascii=False)
            }]
        })

        backlog = result["structured_response"].backlog_millions

        _logger.info(f"{company_name}'s backlog found.")
        return backlog
