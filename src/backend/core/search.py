from llama_index.core import Document, VectorStoreIndex
from llama_index.llms.openai import OpenAI
from sqlalchemy import select

from backend.database.database import SessionFactory
from backend.database.models import StockModel


async def rag(query: str) -> dict:
    with SessionFactory() as db:
        stocks_query = select(StockModel.ticker, StockModel.annual_report)
        stocks = db.execute(stocks_query).all()

        documents = [
            Document(
                text=stock.annual_report,
                metadata={"ticker": stock.ticker}
            )
            for stock in stocks
        ]

    index = VectorStoreIndex.from_documents(documents)

    query_engine = index.as_query_engine(
        llm=OpenAI(model="gpt-5.6-luna")
    )

    response = query_engine.query(query)

    result = {
        "result": response.response,
        "sources": []
    }

    for source in response.source_nodes:
        result["sources"].append({
            "score": source.score,
            "source": source.node.get_content()
        })

    return result
