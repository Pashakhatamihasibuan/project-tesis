"""
Wrapper untuk 3 model embedding yang dibandingkan di penelitian:
Multilingual-E5-small, Paraphrase-multilingual-MPNET, LaBSE.

CATATAN: saat pertama kali dipanggil, sentence-transformers akan
mengunduh bobot model dari huggingface.co (perlu koneksi internet).
Setelah pertama kali, model di-cache lokal dan bisa dipakai offline.
Ini konsisten dengan prinsip "local RAG" -- unduh sekali, jalankan
seterusnya tanpa API berbayar/tanpa panggilan cloud berulang.
"""
import numpy as np

from app.embedding.base import BaseEmbedder
from app.config import settings


class SentenceTransformerEmbedder(BaseEmbedder):
    _model_cache = {}  # class-level cache supaya tidak load ulang tiap instansiasi

    def __init__(self, model_key: str):
        if model_key not in settings.embedding_models:
            raise ValueError(f"model_key tidak dikenal: {model_key}")

        self.name = model_key
        model_name = settings.embedding_models[model_key]

        if model_name not in self._model_cache:
            from sentence_transformers import SentenceTransformer
            self._model_cache[model_name] = SentenceTransformer(model_name)

        self.model = self._model_cache[model_name]
        self.dim = self.model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        # E5 butuh prefix "query: " / "passage: " sesuai paper aslinya
        if self.name == "e5_small":
            texts = [f"passage: {t}" for t in texts]
        embeddings = self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        if self.name == "e5_small":
            query = f"query: {query}"
        return self.model.encode([query], normalize_embeddings=True, convert_to_numpy=True)[0].astype(np.float32)
