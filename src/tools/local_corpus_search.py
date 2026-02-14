"""Hybrid local corpus search for offline/online research.

This module implements hybrid retrieval over a local corpus using:
- Keyword ranking (term-frequency based)
- Semantic similarity (sentence embeddings)

When semantic dependencies are unavailable, the system degrades gracefully to
keyword-only mode to preserve offline-first behavior.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency path
    np = None


@dataclass
class SearchResult:
    title: str
    source: str
    snippet: str
    published_at: str
    score: float = 0.0
    keyword_score: float = 0.0
    semantic_score: float = 0.0


class LocalCorpusSearch:
    """Searches local corpus using hybrid semantic + keyword retrieval."""

    _shared_embed_model = None

    def __init__(
        self,
        corpus_dir: Path | None = None,
        semantic_weight: float = 0.6,
        vector_backend: str = "faiss",
        vector_store_dir: Optional[Path] = None,
    ):
        if corpus_dir is None:
            # Path relative to project root; can be overridden in tests
            corpus_dir = Path(__file__).resolve().parent.parent / "data" / "corpus"
        self.corpus_dir = corpus_dir
        self.semantic_weight = semantic_weight
        self.keyword_weight = 1.0 - semantic_weight
        self.vector_backend = (vector_backend or "chroma").lower()
        self.vector_store_dir = vector_store_dir or (self.corpus_dir / ".vector_store")
        self._documents: List[Dict[str, str]] = []
        self._embeddings = None
        self._semantic_available = False
        self._embed_model = None
        self._faiss_index = None
        self._chroma_collection = None

        self._load_documents()
        self._init_semantic_index()

    def _load_documents(self) -> None:
        self._documents = []
        for file_path in self.corpus_dir.glob("*.*"):
            try:
                text = file_path.read_text(encoding="utf-8")
            except Exception:
                continue

            title = file_path.stem
            published_at = ""
            body = text
            if text.lstrip().startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    front = parts[1]
                    body = parts[2]
                    for line in front.splitlines():
                        if ":" in line:
                            key, value = line.split(":", 1)
                            key = key.strip().lower()
                            value = value.strip()
                            if key == "title":
                                title = value
                            elif key == "published_at":
                                published_at = value

            self._documents.append(
                {
                    "title": title,
                    "published_at": published_at or datetime.now().date().isoformat(),
                    "body": body,
                    "source": file_path.as_uri(),
                }
            )

    def _init_semantic_index(self) -> None:
        if not self._documents:
            return
        if np is None:
            self._semantic_available = False
            return

        try:
            from sentence_transformers import SentenceTransformer

            if LocalCorpusSearch._shared_embed_model is None:
                LocalCorpusSearch._shared_embed_model = SentenceTransformer(
                    "all-MiniLM-L6-v2"
                )
                try:
                    LocalCorpusSearch._shared_embed_model.max_seq_length = 256
                except Exception:
                    pass

            self._embed_model = LocalCorpusSearch._shared_embed_model
            texts = [doc["body"][:4000] for doc in self._documents]
            embeddings = self._embed_model.encode(texts, normalize_embeddings=True)
            self._embeddings = np.array(embeddings, dtype=np.float32)

            if self.vector_backend == "faiss":
                self._init_faiss_index()
            elif self.vector_backend == "chroma":
                self._init_chroma_collection(texts)

            self._semantic_available = True
        except Exception:
            self._embed_model = None
            self._embeddings = None
            self._faiss_index = None
            self._chroma_collection = None
            self._semantic_available = False

    def _init_faiss_index(self) -> None:
        if np is None or self._embeddings is None:
            return
        try:
            import faiss

            dim = int(self._embeddings.shape[1])
            index = faiss.IndexFlatIP(dim)
            index.add(self._embeddings)
            self._faiss_index = index
        except Exception:
            self._faiss_index = None

    def _init_chroma_collection(self, texts: List[str]) -> None:
        try:
            import chromadb
            from chromadb.config import Settings

            self.vector_store_dir.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(
                path=str(self.vector_store_dir.resolve()),
                settings=Settings(anonymized_telemetry=False),
            )
            collection = client.get_or_create_collection(name="local_corpus")

            existing = 0
            try:
                existing = collection.count()
            except Exception:
                existing = 0

            if existing == 0:
                ids = [f"doc-{i}" for i in range(len(texts))]
                metadatas = [
                    {
                        "title": doc["title"],
                        "published_at": doc["published_at"],
                        "source": doc["source"],
                    }
                    for doc in self._documents
                ]
                collection.add(documents=texts, ids=ids, metadatas=metadatas)

            self._chroma_collection = collection
        except Exception:
            self._chroma_collection = None

    @staticmethod
    def _keyword_score(query_terms: List[str], body: str) -> float:
        lower_body = body.lower()
        return float(sum(lower_body.count(term) for term in query_terms))

    def _semantic_scores(self, query: str) -> List[float]:
        if (
            not self._semantic_available
            or self._embed_model is None
            or self._embeddings is None
        ):
            return [0.0] * len(self._documents)
        if np is None:
            return [0.0] * len(self._documents)

        try:
            if self.vector_backend == "faiss" and self._faiss_index is not None:
                return self._semantic_scores_faiss(query)
            if self.vector_backend == "chroma" and self._chroma_collection is not None:
                chroma_scores = self._semantic_scores_chroma(query)
                if any(score > 0 for score in chroma_scores):
                    return chroma_scores

            query_embedding = self._embed_model.encode(
                [query], normalize_embeddings=True
            )
            query_vec = np.array(query_embedding[0], dtype=np.float32)
            similarities = np.dot(self._embeddings, query_vec)
            return [float(max(0.0, s)) for s in similarities]
        except Exception:
            return [0.0] * len(self._documents)

    def _semantic_scores_faiss(self, query: str) -> List[float]:
        if np is None or self._faiss_index is None or self._embed_model is None:
            return [0.0] * len(self._documents)
        try:
            query_embedding = self._embed_model.encode(
                [query], normalize_embeddings=True
            )
            query_vec = np.array(query_embedding, dtype=np.float32)
            distances, indices = self._faiss_index.search(
                query_vec, len(self._documents)
            )

            scores = [0.0] * len(self._documents)
            for rank_idx, doc_idx in enumerate(indices[0]):
                if doc_idx < 0 or doc_idx >= len(self._documents):
                    continue
                scores[int(doc_idx)] = float(max(0.0, distances[0][rank_idx]))
            return scores
        except Exception:
            return [0.0] * len(self._documents)

    def _semantic_scores_chroma(self, query: str) -> List[float]:
        if self._chroma_collection is None:
            return [0.0] * len(self._documents)

        try:
            response = self._chroma_collection.query(
                query_texts=[query],
                n_results=min(len(self._documents), 20),
            )
            ids = response.get("ids", [[]])[0]
            distances = response.get("distances", [[]])[0]

            scores = [0.0] * len(self._documents)
            for doc_id, distance in zip(ids, distances):
                if not doc_id.startswith("doc-"):
                    continue
                idx = int(doc_id.split("-", 1)[1])
                if 0 <= idx < len(scores):
                    similarity = max(0.0, 1.0 - float(distance))
                    scores[idx] = similarity
            return scores
        except Exception:
            return [0.0] * len(self._documents)

    @staticmethod
    def _normalize(scores: List[float]) -> List[float]:
        if not scores:
            return []
        high = max(scores)
        low = min(scores)
        if high == low:
            return [1.0 if high > 0 else 0.0 for _ in scores]
        return [(score - low) / (high - low) for score in scores]

    @staticmethod
    def _snippet(body: str, query_terms: List[str], max_len: int = 200) -> str:
        if not body:
            return ""
        lower_body = body.lower()
        start_idx = 0
        for term in query_terms:
            found = lower_body.find(term)
            if found >= 0:
                start_idx = found
                break
        return body[start_idx : start_idx + max_len].replace("\n", " ")

    def search(self, query: str, k: int = 5) -> List[SearchResult]:
        """Return up to `k` documents ranked by hybrid semantic+keyword score."""
        terms = [t.lower() for t in re.findall(r"\w+", query)]
        if not self._documents:
            return []

        keyword_scores = [
            self._keyword_score(terms, doc["body"]) for doc in self._documents
        ]
        semantic_scores = self._semantic_scores(query)

        keyword_norm = self._normalize(keyword_scores)
        semantic_norm = self._normalize(semantic_scores)

        ranked: List[Tuple[int, float, float, float]] = []
        for idx, doc in enumerate(self._documents):
            combined = (keyword_norm[idx] * self.keyword_weight) + (
                semantic_norm[idx] * self.semantic_weight
            )
            if combined <= 0.0:
                continue
            ranked.append((idx, combined, keyword_scores[idx], semantic_scores[idx]))

        ranked.sort(key=lambda row: row[1], reverse=True)

        results: List[SearchResult] = []
        for idx, combined_score, keyword_score, semantic_score in ranked[:k]:
            doc = self._documents[idx]
            results.append(
                SearchResult(
                    title=doc["title"],
                    source=doc["source"],
                    snippet=self._snippet(doc["body"], terms),
                    published_at=doc["published_at"],
                    score=combined_score,
                    keyword_score=keyword_score,
                    semantic_score=semantic_score,
                )
            )

        return results[:k]
