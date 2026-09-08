import json
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import structlog


SYSTEM_PROMPT = """
You are an expert financial analyst. Your job is to answer how big a company's
backlog is based on the web pages provided.
"""


_logger = structlog.get_logger(__name__)


class BacklogResult(BaseModel):
    backlog_millions: int = Field(
        description="The company's backlog in millions of USD, "
                    "or 0 if unavailable."
    )


class BacklogFinder:
    def __init__(self):
        model = ChatOpenAI(
            model="gpt-5.6-luna",
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
        _logger.info("Running backlog finder agent.", prompt_size=len(prompt))

        result = await self._agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": prompt
            }]
        })

        backlog = result["structured_response"].backlog_millions

        _logger.info(f"{company_name}'s backlog is {backlog}.")
        return backlog
