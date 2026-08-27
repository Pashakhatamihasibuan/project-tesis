"""
Embedder berbasis hashing sederhana (bag-of-words hashed ke vektor
tetap). BUKAN untuk skripsi/produksi -- hanya untuk memvalidasi bahwa
seluruh pipeline (chunking -> index -> retrieval -> RAG) bisa jalan
end-to-end di lingkungan yang belum punya akses ke HuggingFace.

Ganti ke SentenceTransformerEmbedder (e5_small.py / mpnet.py / labse.py)
begitu kamu menjalankan sistem ini di mesin dengan akses internet.
"""
import re
import numpy as np

from app.embedding.base import BaseEmbedder


class DummyHashEmbedder(BaseEmbedder):
    def __init__(self, dim: int = 384):
        self.name = "dummy_hash"
        self.dim = dim

    def _hash_token(self, token: str) -> int:
        return abs(hash(token)) % self.dim

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            tokens = re.findall(r"\w+", text.lower())
            for tok in tokens:
                vectors[i, self._hash_token(tok)] += 1.0
            norm = np.linalg.norm(vectors[i])
            if norm > 0:
                vectors[i] /= norm
        return vectors
