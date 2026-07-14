from langchain.agents import create_agent

from core.tools.web import load_web_page
from core.tools.brave_search import web_search


COMPANY_SCOUT_PROMPT = """
You are a helpful assistant.
"""


class CompanyScout:
    def __init__(self):
        self._agent = create_agent(
            model="openai:gpt-5.4-nano",
            tools=[load_web_page, web_search],
            system_prompt=COMPANY_SCOUT_PROMPT
        )
    
    async def run(self) -> list:
        result = await self._agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": "What's the capital of France?"
            }]
        })

        return result["messages"][-1].content