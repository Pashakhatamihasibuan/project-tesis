import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth.rbac_middleware import get_current_user_optional
from app.auth.models import User
from app.history.chat_history import save_history_if_logged_in, get_recent_turns_for_context
from app.rag.pipeline_factory import get_pipeline, get_embedder
from app.vectorstore.store_manager import StoreManager
from app.core.rate_limit import limiter
from app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

# StoreManager dibangun sekali di awal (lihat scripts/build_official_index.py),
# lalu dipakai bersama di seluruh request. Di produksi ini idealnya di-load
# dari index yang sudah disimpan (turbovec .tvim + doc_store.sqlite3).
_store_manager = StoreManager()


class ChatRequest(BaseModel):
    query: str
    architecture: str = "standard"   # "standard" | "hyde" | "rerank"
    embedding: str = "e5_small"      # "e5_small" | "mpnet" | "labse"


def _build_query_with_context(query: str, history_turns: list[dict]) -> str:
    """
    Gabungkan beberapa giliran percakapan terakhir sebagai konteks
    sebelum query dikirim ke pipeline RAG. Tanpa ini, tiap pertanyaan
    diproses independen -- pertanyaan lanjutan seperti "berapa lama
    pengerjaannya?" tidak nyambung ke konteks "tesis" yang disebut di
    pertanyaan sebelumnya.

    Desain sengaja SEDERHANA (concatenation, bukan reformulasi via LLM
    terpisah): riwayat ditempel sebagai konteks tambahan di depan
    pertanyaan baru, retrieval tetap dijalankan atas gabungan teks ini.
    Pendekatan reformulasi query berbasis LLM (query rewriting) adalah
    pengembangan lanjutan yang bisa disebut di bab saran penelitian
    selanjutnya, di luar cakupan penelitian ini.
    """
    if not history_turns:
        return query

    context_lines = []
    for turn in history_turns:
        context_lines.append(f"Pertanyaan sebelumnya: {turn['question']}")
        context_lines.append(f"Jawaban sebelumnya: {turn['answer'][:300]}")

    context_block = "\n".join(context_lines)
    return (
        f"[Riwayat percakapan sebelumnya, untuk konteks]\n{context_block}\n\n"
        f"[Pertanyaan baru dari pengguna]\n{query}"
    )


@router.post("")
@limiter.limit(settings.rate_limit_chat)
async def chat(
    request: Request,
    payload: ChatRequest,
    current_user: User | None = Depends(get_current_user_optional),
):
    pipeline_fn = get_pipeline(payload.architecture)
    embedder = get_embedder(payload.embedding, use_dummy=False)

    # Multi-turn context HANYA tersedia untuk user login -- konsisten
    # dengan prinsip riwayat guest tidak pernah disimpan (lihat
    # history/chat_history.py), sehingga guest juga tidak punya
    # konteks lintas-giliran untuk diambil.
    history_turns = []
    if current_user:
        history_turns = get_recent_turns_for_context(current_user.id, limit=settings.max_history_turns)

    query_with_context = _build_query_with_context(payload.query, history_turns)

    async def event_stream():
        full_answer = []
        # use_hybrid=True (default) -- ini mode operasional/chat biasa,
        # BUKAN eksperimen 9 konfigurasi inti (yang memakai
        # use_hybrid=False, lihat evaluation/ragas_runner.py)
        async for event in pipeline_fn(query_with_context, embedder, _store_manager):
            if event["type"] == "token":
                full_answer.append(event["content"])
            yield f"data: {json.dumps(event)}\n\n"

        # Simpan riwayat HANYA jika ada user login. Guest: baris ini
        # tetap dipanggil tapi save_history_if_logged_in langsung
        # return None kalau current_user None -- tidak ada penulisan DB.
        # Catatan: yang disimpan adalah payload.query ASLI (tanpa
        # konteks riwayat yang ditempel), supaya tampilan riwayat chat
        # di UI tetap bersih dan tidak berulang-ulang.
        save_history_if_logged_in(
            user_id=current_user.id if current_user else None,
            question=payload.query,
            answer="".join(full_answer),
            configuration=f"{payload.architecture}+{payload.embedding}",
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")
