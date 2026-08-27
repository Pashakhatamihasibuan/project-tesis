"""
Pipeline chunking utuh:

1. Load PDF (native text + tandai halaman yang perlu OCR)
2. Jalankan OCR untuk halaman yang perlu
3. Bersihkan teks (header/footer/nomor halaman)
4. Split berdasarkan struktur dokumen (Pasal/BAB) dulu -- baru fallback
   ke recursive character splitting untuk section yang masih kepanjangan
5. Ekstrak tabel secara terpisah sebagai chunk atomic
6. Deduplikasi chunk yang identik
7. Hasil akhir: list[Chunk] siap di-embed
"""
from dataclasses import dataclass, field
import hashlib

from app.config import settings
from app.ingestion.pdf_loader import load_pdf_pages
from app.ingestion.ocr_engine import ocr_pages_needed
from app.ingestion.cleaner import clean_document
from app.ingestion.structure_parser import split_by_legal_structure
from app.ingestion.table_extractor import extract_tables


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source_file: str
    page_number: int
    content_type: str  # "pasal" | "bab" | "prosa" | "table"
    bbox: tuple | None = None
    metadata: dict = field(default_factory=dict)


def _estimate_tokens(text: str) -> int:
    # estimasi kasar: rata-rata 1 token ~ 4 karakter untuk teks Bahasa Indonesia
    return max(1, len(text) // 4)


def _recursive_char_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Fallback split kalau satu section masih lebih panjang dari chunk_size."""
    approx_char_size = chunk_size * 4
    approx_overlap = overlap * 4

    if len(text) <= approx_char_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + approx_char_size
        chunks.append(text[start:end])
        start = end - approx_overlap
    return chunks


def _make_chunk_id(source_file: str, page_number: int, text: str) -> str:
    raw = f"{source_file}:{page_number}:{text[:50]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def chunk_pdf(pdf_path: str) -> list[Chunk]:
    pages = load_pdf_pages(pdf_path)

    # 1. OCR fallback untuk halaman yang text-nya kosong/minim
    ocr_results = ocr_pages_needed(pdf_path, pages) if any(p.needs_ocr for p in pages) else {}
    for p in pages:
        if p.needs_ocr and p.page_number in ocr_results:
            p.text = ocr_results[p.page_number]

    # 2. Cleaning (deteksi header/footer berulang lintas halaman)
    raw_texts = [p.text for p in pages]
    cleaned_texts = clean_document(raw_texts)

    all_chunks: list[Chunk] = []
    seen_hashes: set[str] = set()

    # 3. Structure-aware split per halaman, fallback ke recursive split
    for page, cleaned_text in zip(pages, cleaned_texts):
        if not cleaned_text.strip():
            continue

        sections = split_by_legal_structure(cleaned_text)
        for section in sections:
            token_count = _estimate_tokens(section.text)
            if token_count <= settings.chunk_size_tokens:
                pieces = [section.text]
            else:
                pieces = _recursive_char_split(section.text, settings.chunk_size_tokens, settings.chunk_overlap_tokens)

            for piece in pieces:
                piece = piece.strip()
                if not piece:
                    continue
                text_hash = hashlib.md5(piece.encode("utf-8")).hexdigest()
                if text_hash in seen_hashes:
                    continue  # dedup
                seen_hashes.add(text_hash)

                all_chunks.append(
                    Chunk(
                        chunk_id=_make_chunk_id(pdf_path, page.page_number, piece),
                        text=piece,
                        source_file=pdf_path,
                        page_number=page.page_number,
                        content_type=section.section_type,
                        metadata={"heading": section.heading} if section.heading else {},
                    )
                )

    # 4. Tabel diperlakukan atomic, tidak melalui recursive splitting
    table_chunks = extract_tables(pdf_path)
    for tc in table_chunks:
        text_hash = hashlib.md5(tc.content_markdown.encode("utf-8")).hexdigest()
        if text_hash in seen_hashes:
            continue
        seen_hashes.add(text_hash)
        all_chunks.append(
            Chunk(
                chunk_id=_make_chunk_id(pdf_path, tc.page_number, tc.content_markdown),
                text=tc.content_markdown,
                source_file=tc.source_file,
                page_number=tc.page_number,
                content_type="table",
            )
        )

    return all_chunks
