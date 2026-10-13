from llama_index.core import VectorStoreIndex, SimpleDirectoryReader


async def rag(query: str) -> str:
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)

    query_engine = index.as_query_engine()
    
    return query_engine.query(query).response
