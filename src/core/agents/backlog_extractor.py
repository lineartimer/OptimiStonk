from langchain.agents import create_agent


BACKLOG_EXTRACTOR_PROMPT = """
You are a helpful assistant.
"""


class BacklogExtractor:
    def __init__(self):
        self._agent = create_agent(
            model="openai:gpt-5.4-nano",
            system_prompt=BACKLOG_EXTRACTOR_PROMPT
        )
    
    async def run(self) -> list:
        result = await self._agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": "What's the capital of France?"
            }]
        })

        return result["messages"][-1].content