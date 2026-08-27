from app.retrieval.hybrid_search import hybrid_retrieve
from app.llm.ollama_client import generate_stream
from app.rag.standard_rag import SYSTEM_PROMPT, _build_context, build_citations
from app.config import settings

_cross_encoder_cache = {}


def _get_cross_encoder():
    """Lazy-load cross-encoder (butuh akses HuggingFace saat pertama load)."""
    if "model" not in _cross_encoder_cache:
        from sentence_transformers import CrossEncoder
        _cross_encoder_cache["model"] = CrossEncoder(settings.rerank_model)
    return _cross_encoder_cache["model"]


async def run_rerank_rag(query: str, embedder, store_manager, top_k: int = settings.top_k_default, use_hybrid: bool = True):
    # 1. Initial retrieval dengan kandidat lebih banyak dari top_k final
    candidates = hybrid_retrieve(query, embedder, store_manager, top_k=settings.rerank_initial_k, use_hybrid=use_hybrid)

    # 2. Re-rank kandidat pakai cross-encoder (constant di semua konfigurasi
    #    Re-ranking, supaya variasi performa yang terukur murni dari
    #    perbedaan model embedding di tahap initial retrieval)
    cross_encoder = _get_cross_encoder()
    pairs = [(query, c["text"]) for c in candidates]
    scores = cross_encoder.predict(pairs)

    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    top_chunks = [c for c, _ in ranked[:top_k]]

    context = _build_context(top_chunks)
    prompt = f"Konteks dokumen:\n{context}\n\nPertanyaan: {query}\n\nJawaban:"

    citations = build_citations(top_chunks)

    async for token in generate_stream(prompt, SYSTEM_PROMPT):
        yield {"type": "token", "content": token}

    yield {"type": "citations", "content": citations}
