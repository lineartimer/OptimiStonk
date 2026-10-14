import asyncio

from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.schema import TextNode
from llama_index.llms.openai import OpenAI
from sqlalchemy import delete, select

from backend.database.database import SessionFactory
from backend.database.models import FilingEmbeddingModel, StockModel


async def rag(query: str) -> dict:
    return await asyncio.to_thread(_rag_impl, query)


def _rag_impl(query: str) -> dict:
    embed_model = Settings.embed_model
    pipeline = IngestionPipeline(
        transformations=[Settings.node_parser, embed_model]
    )

    with SessionFactory() as db:
        stocks_query = select(
            StockModel.id,
            StockModel.ticker,
            StockModel.annual_report,
            StockModel.quarterly_report
        )
        stocks = db.execute(stocks_query).all()

    embeddings = []
    for stock in stocks:
        for filing_type, report in [
            ("10-K", stock.annual_report),
            ("10-Q", stock.quarterly_report)
        ]:
            if not report or not report.strip():
                continue

            nodes = pipeline.run(documents=[
                Document(
                    text=report,
                    metadata={"ticker": stock.ticker, "filing_type": filing_type}
                )
            ])

            embeddings.extend(
                FilingEmbeddingModel(
                    stock_id=stock.id,
                    filing_type=filing_type,
                    chunk_index=i,
                    content=node.text,
                    embedding=node.embedding
                )
                for i, node in enumerate(nodes)
            )

    # Replace all stored chunks together, after embedding generation succeeds
    with SessionFactory() as db:
        db.execute(delete(FilingEmbeddingModel))
        db.add_all(embeddings)
        db.commit()

    with SessionFactory() as db:
        rows = db.execute(
            select(FilingEmbeddingModel, StockModel.ticker)
            .join(StockModel, StockModel.id == FilingEmbeddingModel.stock_id)
        ).all()

        nodes = [
            TextNode(
                id_=str(chunk.id),
                text=chunk.content,
                embedding=chunk.embedding,
                metadata={"ticker": ticker, "filing_type": chunk.filing_type}
            )
            for chunk, ticker in rows
        ]

    if not nodes:
        return {"result": "No filings available.", "sources": []}

    index = VectorStoreIndex(nodes, embed_model=embed_model)

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
