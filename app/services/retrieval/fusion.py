from langchain_core.documents import Document

from app.constants import RRF_K_CONSTANT


def _doc_key(doc: Document) -> tuple:
    return (doc.metadata.get("source"), doc.metadata.get("heading"))


def rrf_fuse(
    rankings: list[list[tuple[Document, float]]], k: int = RRF_K_CONSTANT
) -> list[tuple[Document, float]]:
    scores: dict[tuple, float] = {}
    doc_by_key: dict[tuple, Document] = {}
    for ranking in rankings:
        for rank, (doc, _) in enumerate(ranking, start=1):
            key = _doc_key(doc)
            doc_by_key[key] = doc
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
    ranked_keys = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [(doc_by_key[key], score) for key, score in ranked_keys]
