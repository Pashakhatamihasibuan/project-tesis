"""
Wrapper di atas turbovec.IdMapIndex.

Kenapa IdMapIndex (bukan TurboQuantIndex polos): kita perlu ID eksternal
sendiri (uint64) yang bisa dipetakan ke chunk_id di doc_store.py --
IdMapIndex mendukung ini lewat add_with_ids().
"""
import numpy as np
import turbovec


class TurboVecStore:
    def __init__(self, dim: int | None = None, bit_width: int = 4):
        """
        bit_width=4 direkomendasikan TurboVec sebagai default
        (keseimbangan recall vs memori). Naikkan ke 8 kalau butuh presisi
        lebih tinggi, turunkan ke 2 kalau memori sangat terbatas.
        """
        self.index = turbovec.IdMapIndex(dim=dim, bit_width=bit_width)

    def add(self, vectors: np.ndarray, ids: np.ndarray):
        """
        vectors: shape (n, dim) float32
        ids: shape (n,) uint64 -- gunakan hash chunk_id yang konsisten
        """
        vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        ids = np.ascontiguousarray(ids, dtype=np.uint64)
        self.index.add_with_ids(vectors, ids)

    def search(self, query_vector: np.ndarray, top_k: int, allowlist: np.ndarray | None = None):
        """
        Return (scores, ids) masing-masing shape (1, effective_k).
        """
        query_vector = np.ascontiguousarray(query_vector.reshape(1, -1), dtype=np.float32)
        scores, ids = self.index.search(query_vector, top_k, allowlist=allowlist)
        return scores[0], ids[0]

    def __len__(self):
        return len(self.index)

    def save(self, path: str):
        self.index.write(path)

    @classmethod
    def load(cls, path: str) -> "TurboVecStore":
        obj = cls.__new__(cls)
        obj.index = turbovec.IdMapIndex.load(path)
        return obj
