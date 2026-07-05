# mcp_chroma_server.py
import sys
from mcp.server.fastmcp import FastMCP
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
import chromadb

mcp = FastMCP("Local Vector DB Search")

# Connection to the same shared database
embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://localhost:11434")
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
vector_store = Chroma(client=chroma_client, collection_name="local_knowledge_base", embedding_function=embeddings)

@mcp.tool()
def query_local_documents(query: str, n_results: int = 4) -> str:
    """
    Search across the local internal knowledge base documents for relevant context.
    Use this whenever the user asks questions about reports, guides, or local policies.
    """
    results = vector_store.similarity_search(query, k=n_results)
    
    formatted_context = []
    for doc in results:
        meta = doc.metadata
        formatted_context.append(
            f"--- Context Segment ---\n"
            f"Doc ID: {meta.get('source_id')}\n"
            f"Description: {meta.get('description')}\n"
            f"Path: {meta.get('file_path')}\n"
            f"Content:\n{doc.page_content}\n"
        )
    return "\n".join(formatted_context) if formatted_context else "No matching documents found."

if __name__ == "__main__":
    mcp.run(transport='stdio')