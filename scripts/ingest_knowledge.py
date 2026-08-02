"""Build (or rebuild) the local Qdrant policy collection.

Usage:
    uv run python scripts/ingest_knowledge.py
"""

from strideguard.retrieval import create_or_replace_store
from strideguard.settings import get_settings


def main() -> None:
    settings = get_settings()
    store = create_or_replace_store(settings)
    print(f"Ingested policies into collection {settings.qdrant_collection!r}")
    print(f"Local Qdrant path: {settings.qdrant_path}")
    _ = store


if __name__ == "__main__":
    main()
