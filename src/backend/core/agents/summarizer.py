import json
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import structlog


SYSTEM_PROMPT = """
You are an expert financial analyst. Your job is to create a summary
introducing the given company based on the SEC filings provided.
"""

_logger = structlog.get_logger(__name__)


class SummaryResult(BaseModel):
    summary: str = Field(
        description="A summary that introduces the company."
    )


class Summarizer:
    def __init__(self):
        model = ChatOpenAI(
            model="gpt-5.6-luna",
            use_responses_api=True,
            reasoning_effort="medium"
        )

        self._agent = create_agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            response_format=ToolStrategy(SummaryResult)
        )
    
    async def run(self, company_name: str, prompt: dict) -> int:
        prompt = json.dumps(prompt, ensure_ascii=False)
        _logger.info("Running summarizer agent.", prompt_size=len(prompt))

        result = await self._agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": prompt
            }]
        })

        summary = result["structured_response"].summary

        _logger.info(f"Summary of {company_name}: {summary[:20]}...")
        return summary
