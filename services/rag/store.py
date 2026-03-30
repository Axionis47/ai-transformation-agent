from __future__ import annotations

# chromadb is imported ONLY in this file — never anywhere else
import chromadb
from chromadb.utils import embedding_functions

_COLLECTION_NAME = "wins_kb"
_singleton: "RAGStore | None" = None


def get_rag_store(persist_dir: str = "./data/chroma_store") -> "RAGStore":
    """Return a module-level singleton RAGStore.

    Prevents multiple ChromaDB clients from fighting over the same
    SQLite file, which causes locking errors in tests and under
    concurrent requests.
    """
    global _singleton
    if _singleton is None:
        _singleton = RAGStore(persist_dir=persist_dir)
    return _singleton


class RAGStore:
    """Abstraction layer over ChromaDB for the Wins Knowledge Base."""

    def __init__(self, persist_dir: str = "./data/chroma_store") -> None:
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._ef = embedding_functions.DefaultEmbeddingFunction()
        self._col = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._ef,
        )

    def add_documents(self, docs: list[dict]) -> int:
        """
        Add documents to the collection.
        Each doc must have: id (str), text (str), metadata (dict).
        Returns count of documents added.
        """
        ids = [d["id"] for d in docs]
        texts = [d["text"] for d in docs]
        metadatas = [d["metadata"] for d in docs]
        self._col.upsert(ids=ids, documents=texts, metadatas=metadatas)
        return len(docs)

    def query(self, query_text: str, top_k: int = 5) -> list[dict]:
        """
        Semantic search. Returns list of {id, text, metadata, score}.
        Score = 1 - distance (cosine similarity).
        """
        results = self._col.query(
            query_texts=[query_text],
            n_results=min(top_k, max(self._col.count(), 1)),
            include=["documents", "metadatas", "distances"],
        )
        output = []
        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]
        for i, doc_id in enumerate(ids):
            output.append(
                {
                    "id": doc_id,
                    "text": docs[i],
                    "metadata": metas[i],
                    "score": 1.0 - dists[i],
                }
            )
        return output

    def count(self) -> int:
        """Return number of documents in collection."""
        return self._col.count()

    def clear(self) -> None:
        """Delete and recreate collection (used in tests)."""
        self._client.delete_collection(_COLLECTION_NAME)
        self._col = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._ef,
        )
