from app.retrieval.hybrid_search import hybrid_retrieve
from app.llm.ollama_client import generate_stream, generate_once
from app.rag.standard_rag import SYSTEM_PROMPT, _build_context, build_citations
from app.config import settings

HYDE_PROMPT_TEMPLATE = (
    "Tuliskan satu paragraf jawaban HIPOTETIS (perkiraan, tidak perlu akurat) "
    "untuk pertanyaan berikut, seolah-olah itu adalah kutipan dari dokumen "
    "resmi akademik. Ini hanya dipakai untuk membantu pencarian dokumen, "
    "bukan jawaban final.\n\nPertanyaan: {query}"
)


async def run_hyde_rag(query: str, embedder, store_manager, top_k: int = settings.top_k_default, use_hybrid: bool = True):
    # 1. Generate dokumen hipotetis (panggilan LLM tambahan -- inilah
    #    kenapa HyDE lebih lambat dari Standard RAG)
    hyde_prompt = HYDE_PROMPT_TEMPLATE.format(query=query)
    hypothetical_doc = await generate_once(hyde_prompt)

    # 2. Retrieval pakai embedding dari dokumen hipotetis, BUKAN query asli
    chunks = hybrid_retrieve(hypothetical_doc, embedder, store_manager, top_k=top_k, use_hybrid=use_hybrid)
    context = _build_context(chunks)

    # 3. Generate jawaban final pakai query asli + context asli
    final_prompt = f"Konteks dokumen:\n{context}\n\nPertanyaan: {query}\n\nJawaban:"

    citations = build_citations(chunks)

    async for token in generate_stream(final_prompt, SYSTEM_PROMPT):
        yield {"type": "token", "content": token}

    yield {"type": "citations", "content": citations}
