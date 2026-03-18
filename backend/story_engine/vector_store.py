import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from backend.config.settings import CHROMA_PATH


COLLECTION_NAME = "classical_story_chunks"
CHUNK_DATA_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "classical_story_chunks.json"
)


class ClassicalStoryVectorStore:
    def __init__(self, chroma_path: str | None = None) -> None:
        try:
            import chromadb
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Chroma vector store is unavailable in this environment. "
                    "Check the installed chromadb and numpy builds."
                ),
            ) from exc

        self._client = chromadb.PersistentClient(path=chroma_path or CHROMA_PATH)
        self._collection = self._load_or_bootstrap_collection(chromadb)

    def _load_or_bootstrap_collection(self, chromadb_module: Any) -> Any:
        try:
            collection = self._client.get_collection(name=COLLECTION_NAME)
        except chromadb_module.errors.NotFoundError:
            collection = self._client.get_or_create_collection(name=COLLECTION_NAME)
            self._bootstrap_collection(collection)
            return collection

        if collection.count() == 0:
            self._bootstrap_collection(collection)

        return collection

    def _bootstrap_collection(self, collection: Any) -> None:
        if not CHUNK_DATA_PATH.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Classical story chunk data is missing. "
                    "Run the classical story import before generating stories."
                ),
            )

        try:
            chunks = json.loads(CHUNK_DATA_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Classical story chunk data could not be loaded",
            ) from exc

        if not isinstance(chunks, list) or not chunks:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Classical story chunk data is empty",
            )

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, str | int]] = []

        for index, chunk in enumerate(chunks, start=1):
            if not isinstance(chunk, dict):
                continue

            text_chunk = chunk.get("text_chunk")
            if not isinstance(text_chunk, str) or not text_chunk.strip():
                continue

            story_id = chunk.get("story_id")
            ids.append(f"story-{story_id or 'unknown'}-chunk-{index}")
            documents.append(text_chunk.strip())
            metadatas.append(
                {
                    "story_id": int(story_id) if isinstance(story_id, int) else -1,
                    "title": str(chunk.get("title") or ""),
                    "author": str(chunk.get("author") or ""),
                    "themes": json.dumps(chunk.get("themes", []), ensure_ascii=False),
                }
            )

        if not ids:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Classical story chunk data did not contain usable text chunks",
            )

        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def query(self, query_text: str, top_k: int = 5) -> list[dict[str, Any]]:
        result = self._collection.query(
            query_texts=[query_text],
            n_results=min(top_k, 5),
            include=["documents", "metadatas", "distances"],
        )

        documents = result.get("documents", [[]])
        metadatas = result.get("metadatas", [[]])
        distances = result.get("distances", [[]])

        rows: list[dict[str, Any]] = []
        for document, metadata, distance in zip(
            documents[0] if documents else [],
            metadatas[0] if metadatas else [],
            distances[0] if distances else [],
        ):
            rows.append(
                {
                    "text_chunk": document,
                    "metadata": metadata or {},
                    "distance": distance,
                }
            )
        return rows
