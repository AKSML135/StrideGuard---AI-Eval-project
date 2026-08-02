from collections.abc import Sequence
from pathlib import Path
from typing import Any

from strideguard.knowledge import load_policy_sections
from strideguard.settings import Settings, get_settings


def build_embeddings(settings: Settings | None = None) -> Any:
    settings = settings or get_settings()
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        encode_kwargs={"normalize_embeddings": True},
    )


# The first execution downloads the embedding model. Subsequent use is local
# and does not consume a cloud embedding API.


def sections_to_documents(policy_dir: Path) -> list[Any]:
    from langchain_core.documents import Document

    return [
        Document(
            page_content=str(section["text"]),
            metadata={
                "doc_id": section["doc_id"],
                "title": section["title"],
                "source": section["source"],
                "version": section["version"],
            },
        )
        for section in load_policy_sections(policy_dir)
    ]


# Stable document IDs are more important than raw chunk text because golden
# cases can name expected evidence.


# The companion implementation uses a file-backed local Qdrant client.
def create_or_replace_store(settings: Settings | None = None) -> Any:
    settings = settings or get_settings()

    from langchain_qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams

    embeddings = build_embeddings(settings)
    documents = sections_to_documents(
        settings.project_root / "knowledge" / "policies"
    )
    vector_size = len(embeddings.embed_query("dimension probe"))

    settings.qdrant_path.mkdir(parents=True, exist_ok=True)
    client = QdrantClient(path=str(settings.qdrant_path))

    if client.collection_exists(settings.qdrant_collection):
        client.delete_collection(settings.qdrant_collection)

    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )

    store = QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection,
        embedding=embeddings,
    )
    store.add_documents(documents=documents)
    return store


# NOTE: `open_store` is called by `retrieve()` below whenever no store is
# passed in, but the guide never prints its body -- only `create_or_replace_store`
# (which rebuilds the collection from scratch during ingestion). Reconstructed
# here as the read-only counterpart: it opens the existing on-disk collection
# without deleting or re-adding documents.
def open_store(settings: Settings | None = None) -> Any:
    settings = settings or get_settings()

    from langchain_qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient

    embeddings = build_embeddings(settings)
    client = QdrantClient(path=str(settings.qdrant_path))
    return QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection,
        embedding=embeddings,
    )


def retrieve(
    query: str,
    *,
    k: int = 4,
    store: Any | None = None,
) -> list[Any]:
    store = store or open_store()
    return store.similarity_search(query, k=k)


def recall_at_k(
    expected_ids: set[str],
    retrieved_ids: Sequence[str],
    k: int,
) -> float:
    if not expected_ids:
        return 1.0
    top_k = set(retrieved_ids[:k])
    return len(expected_ids & top_k) / len(expected_ids)


def reciprocal_rank(
    expected_ids: set[str],
    retrieved_ids: Sequence[str],
) -> float:
    for index, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in expected_ids:
            return 1.0 / index
    return 0.0
