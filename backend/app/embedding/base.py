"""
Interface embedding model. Semua wrapper (E5, MPNet, LaBSE, dummy)
mengikuti kontrak yang sama supaya bisa saling ditukar via
pipeline_factory.py tanpa mengubah kode RAG di atasnya.
"""
from abc import ABC, abstractmethod
import numpy as np


class BaseEmbedder(ABC):
    name: str
    dim: int

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Return array shape (n, dim), dtype float32."""
        ...

    def embed_query(self, query: str) -> np.ndarray:
        return self.embed_texts([query])[0]
