"""
Reciprocal Rank Fusion (RRF) untuk menggabungkan hasil semantic search
(TurboVec) dan keyword search (BM25). Berguna khusus untuk query yang
mengandung kode/istilah persis (nomor pasal, kode matkul) yang kadang
kurang match secara embedding semantik murni.
"""
from app.vectorstore.store_manager import StoreManager


def reciprocal_rank_fusion(
    semantic_ids: list[int],
    keyword_ids: list[int],
    k: int = 60,
) -> list[int]:
    """
    RRF score untuk id yang muncul di rank r (1-indexed) pada satu daftar:
        score += 1 / (k + r)
    Semakin tinggi rank (semakin kecil r), semakin besar kontribusinya.
    k=60 adalah nilai default yang umum dipakai di literatur IR.
    """
    scores: dict[int, float] = {}

    for rank, vid in enumerate(semantic_ids, start=1):
        scores[vid] = scores.get(vid, 0.0) + 1.0 / (k + rank)

    for rank, vid in enumerate(keyword_ids, start=1):
        scores[vid] = scores.get(vid, 0.0) + 1.0 / (k + rank)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [vid for vid, _ in ranked]


def hybrid_retrieve(
    query: str,
    embedder,
    store_manager: StoreManager,
    top_k: int = 5,
    semantic_k: int = 15,
    keyword_k: int = 15,
    use_hybrid: bool = True,
) -> list[dict]:
    """
    Return list of chunk dict (dari doc_store) hasil fusion, sudah
    diurutkan dari paling relevan.

    use_hybrid=False -> retrieval MURNI SEMANTIK (TurboVec saja, BM25
    di-skip total). WAJIB dipakai saat menjalankan evaluasi RAGAS pada
    sembilan konfigurasi inti penelitian, sesuai Bab I.F.4 (cakupan
    penelitian membatasi variabel yang diuji hanya arsitektur RAG dan
    model embedding -- hybrid search adalah fitur pelengkap operasional
    di luar cakupan eksperimen, dipakai use_hybrid=True hanya untuk
    mode chat biasa/produksi).
    """
    model_key = embedder.name
    turbovec_store = store_manager.get_turbovec_store(model_key)
    doc_store = store_manager.doc_store

    query_vector = embedder.embed_query(query)
    _, semantic_ids = turbovec_store.search(query_vector, top_k=semantic_k if use_hybrid else top_k)
    semantic_ids = [int(i) for i in semantic_ids]

    if not use_hybrid:
        results = []
        for vid in semantic_ids[:top_k]:
            chunk = doc_store.get_by_vector_id(vid, model_key)
            if chunk:
                results.append(chunk)
        return results

    bm25_store = store_manager.get_bm25_store(model_key)
    keyword_results = bm25_store.search(query, top_k=keyword_k)
    keyword_ids = [vid for vid, _ in keyword_results]

    fused_ids = reciprocal_rank_fusion(semantic_ids, keyword_ids)[:top_k]

    results = []
    for vid in fused_ids:
        chunk = doc_store.get_by_vector_id(vid, model_key)
        if chunk:
            results.append(chunk)
    return results
