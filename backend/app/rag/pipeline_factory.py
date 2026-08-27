"""
Factory untuk memilih 1 dari 9 kombinasi (3 arsitektur x 3 embedding
model) berdasarkan config yang dipilih user di UI atau saat evaluasi RAGAS.
"""
from app.rag.standard_rag import run_standard_rag
from app.rag.hyde_rag import run_hyde_rag
from app.rag.rerank_rag import run_rerank_rag
from app.embedding.sentence_transformer_embedder import SentenceTransformerEmbedder
from app.embedding.dummy_embedder import DummyHashEmbedder

_PIPELINES = {
    "standard": run_standard_rag,
    "hyde": run_hyde_rag,
    "rerank": run_rerank_rag,
}

_embedder_cache: dict[str, object] = {}


def get_embedder(embedding_key: str, use_dummy: bool = False):
    """
    use_dummy=True dipakai untuk testing/development tanpa akses
    HuggingFace. Set False untuk eksperimen RAGAS sesungguhnya.
    """
    cache_key = f"{embedding_key}_{'dummy' if use_dummy else 'real'}"
    if cache_key not in _embedder_cache:
        if use_dummy:
            _embedder_cache[cache_key] = DummyHashEmbedder()
            _embedder_cache[cache_key].name = embedding_key  # override nama supaya konsisten
        else:
            _embedder_cache[cache_key] = SentenceTransformerEmbedder(embedding_key)
    return _embedder_cache[cache_key]


def get_pipeline(architecture: str):
    if architecture not in _PIPELINES:
        raise ValueError(f"Arsitektur tidak dikenal: {architecture}. Pilihan: {list(_PIPELINES.keys())}")
    return _PIPELINES[architecture]
