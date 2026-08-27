from app.retrieval.hybrid_search import hybrid_retrieve
from app.retrieval.citation_locator import find_bbox_for_text
from app.llm.ollama_client import generate_stream
from app.config import settings

SYSTEM_PROMPT = (
    "Anda adalah AkademiQ, asisten akademik UNY. Jawab HANYA berdasarkan "
    "konteks dokumen resmi yang diberikan. Jika jawaban tidak ada di "
    "konteks, katakan Anda tidak menemukan informasi tersebut di dokumen "
    "resmi -- jangan mengarang."
)


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for c in chunks:
        parts.append(f"[Sumber: {c['source_file']}, hal. {c['page_number']}]\n{c['text']}")
    return "\n\n---\n\n".join(parts)


def build_citations(chunks: list[dict]) -> list[dict]:
    """
    Dipakai bersama oleh standard_rag, hyde_rag, rerank_rag supaya
    format citation (termasuk bbox untuk highlight) konsisten di
    seluruh 9 konfigurasi.
    """
    citations = []
    for c in chunks:
        bbox = find_bbox_for_text(c["source_file"], c["page_number"], c["text"])
        citations.append(
            {
                "source_file": c["source_file"],
                "page_number": c["page_number"],
                "chunk_text": c["text"][:200],
                "bbox": bbox,  # list kosong kalau tidak ketemu (misal halaman hasil OCR)
            }
        )
    return citations


async def run_standard_rag(query: str, embedder, store_manager, top_k: int = settings.top_k_default, use_hybrid: bool = True):
    chunks = hybrid_retrieve(query, embedder, store_manager, top_k=top_k, use_hybrid=use_hybrid)
    context = _build_context(chunks)

    prompt = f"Konteks dokumen:\n{context}\n\nPertanyaan: {query}\n\nJawaban:"

    citations = build_citations(chunks)

    async for token in generate_stream(prompt, SYSTEM_PROMPT):
        yield {"type": "token", "content": token}

    yield {"type": "citations", "content": citations}
