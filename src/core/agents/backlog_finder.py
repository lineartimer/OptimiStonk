from datetime import date
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel, Field
import structlog

from core.tools.brave_search import web_search

SYSTEM_PROMPT = """
You extract a company's latest reported backlog from web search results.

Use the web_search tool with the query "<company name> backlog".

Rules:
1. Only accept a value explicitly attributed to the requested company.
2. Treat "backlog", "order backlog", "order book", "contracted revenue",
   and "remaining performance obligations" (RPO) as equivalent.
3. Prefer the most recently dated result that clearly reports the total backlog.
4. Do not use another company's backlog, market size, revenue, ARR, capex,
   supply commitments, growth amount, or an individual contract value.
5. Prefer a current reported backlog over an older value or future estimate.
6. Convert the value to millions of USD. For example: $678 billion is 678000,
   $900 million is 900, and $1 trillion is 1000000.
7. Return -1 if no defensible company-specific backlog can be found.

Return the result through the required structured response.
"""


USER_PROMPT = """
The current date is {date}.
Company: {company_name}
"""


_logger = structlog.get_logger(__name__)


class BacklogResult(BaseModel):
    backlog_millions: int = Field(
        description="The company's backlog in millions of USD, or -1 if unavailable."
    )


class BacklogFinder:
    def __init__(self):
        self._provider = "openai"
        self._model = "gpt-5.4-nano"
        
        self._agent = create_agent(
            model=f"{self._provider}:{self._model}",
            tools=[web_search],
            system_prompt=SYSTEM_PROMPT,
            response_format=ToolStrategy(BacklogResult),
        )
    
    async def run(self, company_name: str) -> int:
        result = await self._agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": USER_PROMPT.format(
                    company_name=company_name,
                    date=date.today().isoformat()
                )
            }]
        })

        backlog = result["structured_response"].backlog_millions

        _logger.info(
            "Found company backlog.",
            company_name=company_name,
            backlog_millions=backlog,
            model=self._model,
        )

        return backlog
