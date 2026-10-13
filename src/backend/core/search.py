from llama_index.core import VectorStoreIndex, SimpleDirectoryReader


async def rag(query: str) -> dict:
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)

    query_engine = index.as_query_engine()

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
