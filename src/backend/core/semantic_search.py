import asyncio

from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.schema import TextNode
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from sqlalchemy import select

from backend.config import EMBEDDING_MODEL
from backend.database.database import SessionFactory
from backend.database.models import FilingEmbeddingModel, StockModel


class EmbeddingCreationError(Exception):
    pass


async def create_embeddings(
    ticker: str, reports: dict[str, str | None]
) -> list[FilingEmbeddingModel]:
    
    return await asyncio.to_thread(_create_embeddings, ticker, reports)


async def rag(query: str) -> dict:
    return await asyncio.to_thread(_rag_impl, query)


def _create_embeddings(
    ticker: str, reports: dict[str, str | None]
) -> list[FilingEmbeddingModel]:
    
    ticker = ticker.strip().upper()
    filings = [
        (filing_type, report)
        for filing_type, report in [
            ("10-K", reports.get("latest_10k")),
            ("10-Q", reports.get("latest_10q"))
        ]
        if report and report.strip()
    ]

    if not filings:
        return []

    try:
        pipeline = IngestionPipeline(
            transformations=[
                Settings.node_parser,
                OpenAIEmbedding(model=EMBEDDING_MODEL)
            ]
        )

        embeddings = []
        for filing_type, report in filings:
            nodes = pipeline.run(documents=[
                Document(
                    text=report,
                    metadata={"ticker": ticker, "filing_type": filing_type}
                )
            ])

            embeddings.extend(
                FilingEmbeddingModel(
                    filing_type=filing_type,
                    chunk_index=i,
                    content=node.text,
                    embedding=node.embedding
                )
                for i, node in enumerate(nodes)
            )

    except Exception as e:
        raise EmbeddingCreationError(
            f"Failed to create embeddings for {ticker}"
        ) from e

    return embeddings


def _rag_impl(query: str) -> dict:
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
        return {"result": "No filings available", "sources": []}

    index = VectorStoreIndex(
        nodes, embed_model=OpenAIEmbedding(model=EMBEDDING_MODEL)
    )

    query_engine = index.as_query_engine(
        llm=OpenAI(model="gpt-5.6-luna")
    )

    response = query_engine.query(query)

    result = {
        "result": response.response,
        "sources": []
    }

    for source in response.source_nodes:
        metadata = source.node.metadata
        result["sources"].append({
            "title": f"{metadata['ticker']} — latest {metadata['filing_type']}",
            "score": source.score,
            "source": source.node.get_content()
        })

    return result
