"""
Mengelola 3 pasang (TurboVecStore + BM25Store) -- satu pasang per model
embedding yang dibandingkan (e5_small, mpnet, labse). Semua berbagi satu
DocStore SQLite yang sama (dibedakan lewat kolom embedding_model).
"""
import os
import numpy as np

from app.config import settings
from app.vectorstore.turbovec_index import TurboVecStore
from app.vectorstore.bm25_index import BM25Store
from app.vectorstore.doc_store import DocStore, chunk_id_to_uint64


class StoreManager:
    def __init__(self):
        self.doc_store = DocStore(settings.doc_store_db)
        self.turbovec_stores: dict[str, TurboVecStore] = {}
        self.bm25_stores: dict[str, BM25Store] = {}

    def build_index_for_model(self, chunks: list, embedder) -> None:
        """
        chunks: list[Chunk] dari chunker.py
        embedder: instance BaseEmbedder (misal SentenceTransformerEmbedder atau DummyHashEmbedder)
        """
        model_key = embedder.name
        texts = [c.text for c in chunks]
        vectors = embedder.embed_texts(texts)

        ids = np.array([chunk_id_to_uint64(c.chunk_id) for c in chunks], dtype=np.uint64)

        store = TurboVecStore(dim=embedder.dim, bit_width=4)
        store.add(vectors, ids)
        self.turbovec_stores[model_key] = store

        for c in chunks:
            self.doc_store.insert_chunk(c, embedding_model=model_key)

        bm25 = BM25Store()
        bm25.build(self.doc_store.get_all_texts(model_key))
        self.bm25_stores[model_key] = bm25

        os.makedirs(settings.index_dir, exist_ok=True)
        store.save(os.path.join(settings.index_dir, f"{model_key}.tvim"))

    def get_turbovec_store(self, model_key: str) -> TurboVecStore:
        return self.turbovec_stores[model_key]

    def get_bm25_store(self, model_key: str) -> BM25Store:
        return self.bm25_stores[model_key]
