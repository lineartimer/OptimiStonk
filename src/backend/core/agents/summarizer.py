import json
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from backend.core.utils.logger import log_and_stream
from backend.core.utils.message_type import MessageType


SYSTEM_PROMPT = """
You are an expert financial analyst. Your job is to create a summary
introducing the given company based on the SEC filings provided.
"""


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
        log_and_stream(
            "Running summarizer agent.",
            MessageType.info,
            prompt_size=len(prompt))

        result = await self._agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": prompt
            }]
        })

        summary = result["structured_response"].summary

        log_and_stream(
            f"Summary of {company_name}: {summary[:20]}...",
            MessageType.info
        )

        return summary
