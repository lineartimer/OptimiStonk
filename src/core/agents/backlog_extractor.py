from datetime import datetime
from langchain.agents import create_agent


BACKLOG_EXTRACTOR_PROMPT = """
Below you will find the latest 10-K and 10-Q of a company called {company_name}. Your job is to read them and find out, based on these documents, how big is the company's backlog. Look at the Remaining Performance Obligations as well as any future contracts that are not included in that but is discussed in either of the financial statements.

Return the result as a list of json objects. Each backlog item that you can identify should be one such object with a short description of the item, the value of the item expressed in millions of USD, and the time horizon of the item expressed as the number of years from now.

The current date is {date}.

The latest 10-K of {company_name}:

{form_10k}

The latest 10-Q of {company_name}:

{form_10q}
"""


class BacklogExtractor:
    def __init__(self):
        self._agent = create_agent(
            model="openai:gpt-5.4-nano"
        )
    
    async def run(self, company_name: str, form_10k: str, form_10q: str) -> list:
        result = await self._agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": BACKLOG_EXTRACTOR_PROMPT.format(
                    company_name=company_name,
                    date=datetime.now(),
                    form_10k=form_10k,
                    form_10q=form_10q
                )
            }]
        })

        return result["messages"][-1].content