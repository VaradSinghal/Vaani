"""
RAG-less Vector Store — Local embeddings + numpy cosine similarity.

Uses sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) for
multilingual embeddings and numpy for blazing-fast cosine similarity.
No external vector DB needed.

Problem Statement: RAG-less Knowledge Retrieval
- Low latency: ~2ms search over 1000 facts
- Alternative architecture: pre-extracted facts, not raw chunks
- Structured reasoning: LLM reasons over clean facts, not noisy text
"""

import os
import json
import numpy as np
from dataclasses import dataclass, asdict
from typing import Optional
import threading

STORE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vector_store")


@dataclass
class FactEntry:
    text: str
    doc_id: str
    doc_title: str
    doc_type: str


@dataclass
class SearchResult:
    text: str
    score: float
    doc_id: str
    doc_title: str
    doc_type: str


class VectorStore:
    """
    Lightweight local vector store.
    
    RAG-less design:
    - Facts are pre-extracted by LLM at upload time (not raw chunks)
    - Embeddings computed once at upload, not at query time
    - numpy cosine similarity instead of an external vector DB
    - ~2ms search latency for 1000 facts
    """

    def __init__(self):
        self._model = None
        self._model_lock = threading.Lock()
        self.facts: list[FactEntry] = []
        self.embeddings: Optional[np.ndarray] = None  # (N, 384)
        self._initialized = False

    def initialize(self):
        """Force eager loading of the model at startup."""
        self._get_model()
        self._initialized = True

    def _get_model(self):
        """Load the embedding model. Enforces local_files_only for performance."""
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer
                    print("VectorStore: Loading multilingual embedding model (OFFLINE)...")
                    try:
                        self._model = SentenceTransformer(
                            'paraphrase-multilingual-MiniLM-L12-v2',
                            local_files_only=True
                        )
                        print("VectorStore: Model loaded (384-dim, 50+ languages)")
                    except Exception as e:
                        print(f"VectorStore: ERROR - Failed to load model offline: {e}")
                        print("VectorStore: Ensure the model is downloaded to the local cache.")
                        # Fallback for dev if needed (but user requested offline)
                        # self._model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2') 
        return self._model

    def add_facts(self, facts: list[str], doc_id: str, doc_title: str, doc_type: str = "unknown"):
        """
        Embed and store facts. Called once at document upload time.
        
        Args:
            facts: List of atomic fact strings extracted by LLM
            doc_id: Unique document identifier
            doc_title: Human-readable document title
            doc_type: Document type (invoice, receipt, report, etc.)
        """
        if not facts:
            return

        model = self._get_model()
        
        # Compute embeddings for all facts at once (batched = faster)
        new_embeddings = model.encode(facts, normalize_embeddings=True, show_progress_bar=False)
        new_embeddings = np.array(new_embeddings, dtype=np.float32)

        # Create fact entries
        new_entries = [
            FactEntry(text=fact, doc_id=doc_id, doc_title=doc_title, doc_type=doc_type)
            for fact in facts
        ]

        # Append to existing store
        self.facts.extend(new_entries)
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])

        print(f"VectorStore: Added {len(facts)} facts from '{doc_title}' (total: {len(self.facts)})")

    def search(self, query: str, top_k: int = 5, min_score: float = 0.3) -> list[SearchResult]:
        """
        Semantic search over stored facts.
        
        Uses cosine similarity (dot product on normalized vectors).
        Latency: ~2ms for 1000 facts on CPU.
        
        Args:
            query: Natural language query (any language)
            top_k: Number of results to return
            min_score: Minimum similarity threshold
            
        Returns:
            List of SearchResult sorted by relevance
        """
        if not self.facts or self.embeddings is None:
            return []

        model = self._get_model()
        
        # Embed query (single vector, ~5ms)
        query_vec = model.encode(query, normalize_embeddings=True)
        query_vec = np.array(query_vec, dtype=np.float32)

        # Cosine similarity via dot product (vectors are already normalized)
        scores = np.dot(self.embeddings, query_vec)

        # Get top-K indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score < min_score:
                break
            fact = self.facts[idx]
            results.append(SearchResult(
                text=fact.text,
                score=score,
                doc_id=fact.doc_id,
                doc_title=fact.doc_title,
                doc_type=fact.doc_type,
            ))

        return results

    def remove_document(self, doc_id: str):
        """Remove all facts associated with a document."""
        if not self.facts:
            return

        # Find indices to keep
        keep_indices = [i for i, f in enumerate(self.facts) if f.doc_id != doc_id]
        
        if len(keep_indices) == len(self.facts):
            return  # Nothing to remove

        self.facts = [self.facts[i] for i in keep_indices]
        if keep_indices and self.embeddings is not None:
            self.embeddings = self.embeddings[keep_indices]
        else:
            self.embeddings = None

        print(f"VectorStore: Removed facts for doc '{doc_id}' (remaining: {len(self.facts)})")

    def get_documents(self) -> list[dict]:
        """Get a list of unique documents in the store."""
        docs = {}
        for fact in self.facts:
            if fact.doc_id not in docs:
                docs[fact.doc_id] = {
                    "doc_id": fact.doc_id,
                    "title": fact.doc_title,
                    "type": fact.doc_type,
                    "fact_count": 0,
                }
            docs[fact.doc_id]["fact_count"] += 1
        return list(docs.values())

    def save_to_disk(self):
        """Persist vector store to disk."""
        os.makedirs(STORE_DIR, exist_ok=True)

        # Save facts metadata
        facts_data = [asdict(f) for f in self.facts]
        with open(os.path.join(STORE_DIR, "facts.json"), "w", encoding="utf-8") as f:
            json.dump(facts_data, f, ensure_ascii=False, indent=2)

        # Save embeddings
        if self.embeddings is not None:
            np.save(os.path.join(STORE_DIR, "embeddings.npy"), self.embeddings)

        print(f"VectorStore: Saved {len(self.facts)} facts to disk")

    def load_from_disk(self):
        """Load persisted vector store from disk."""
        facts_path = os.path.join(STORE_DIR, "facts.json")
        embeddings_path = os.path.join(STORE_DIR, "embeddings.npy")

        if not os.path.exists(facts_path):
            print("VectorStore: No persisted data found, starting fresh")
            return

        try:
            with open(facts_path, "r", encoding="utf-8") as f:
                facts_data = json.load(f)
            
            self.facts = [FactEntry(**fd) for fd in facts_data]

            if os.path.exists(embeddings_path):
                self.embeddings = np.load(embeddings_path)

            print(f"VectorStore: Loaded {len(self.facts)} facts from disk")
        except Exception as e:
            print(f"VectorStore: Failed to load from disk: {e}")

    @property
    def total_facts(self) -> int:
        return len(self.facts)


# Singleton instance
vector_store = VectorStore()
