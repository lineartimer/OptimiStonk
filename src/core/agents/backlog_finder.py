from datetime import date
from langchain.agents import create_agent
import structlog

SYSTEM_PROMPT = """
"""


USER_PROMPT = """

The current date is {date}.
"""


_logger = structlog.get_logger(__name__)


class BacklogFinder:
    def __init__(self):
        self._provider = "openai"
        self._model = "gpt-5.4-nano"
        
        self._agent = create_agent(
            model=f"{self._provider}:{self._model}",
            system_prompt=SYSTEM_PROMPT
        )
    
    async def run(self, company_name: str) -> int:
        backlog = await self._agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": USER_PROMPT.format(
                    company_name=company_name,
                    date=date.today().isoformat()
                )
            }]
        })

        _logger.info(f"Found backlog for {company_name} using {self._model}.")

        return backlog
