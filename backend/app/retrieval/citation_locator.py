"""
Mencari bounding box (posisi x,y) dari teks chunk di halaman PDF asli,
supaya frontend bisa menggambar highlight (stabilo) tepat di lokasi
jawaban diambil.

Pendekatan: PyMuPDF punya page.search_for(text) yang mencari exact
substring match dan mengembalikan Rect (koordinat). Karena chunk text
bisa panjang/multi-baris (search_for kurang toleran terhadap line break
dan spasi ganda), kita normalisasi whitespace dulu dan coba beberapa
panjang snippet secara bertahap (100 -> 60 -> 40 -> 25 karakter) sampai
ketemu match.

Bbox dikembalikan dalam bentuk TERNORMALISASI (0.0-1.0 relatif terhadap
lebar/tinggi halaman) -- bukan koordinat piksel absolut. Ini penting
supaya frontend bisa memposisikan overlay pakai CSS percentage, tanpa
perlu tahu resolusi/DPI render PDF di browser.

CATATAN: untuk halaman hasil OCR, exact match sering gagal karena teks
hasil OCR tidak identik 100% dengan yang "terlihat" (typo/spasi beda).
Kalau tidak ketemu, sistem tetap mengarahkan ke halaman yang benar,
hanya tanpa highlight -- fallback yang aman, bukan error.
"""
import re
import fitz


def _normalize_snippet(text: str, max_len: int) -> str:
    normalized = " ".join(text.split())
    return normalized[:max_len]


def find_bbox_for_text(pdf_path: str, page_number: int, target_text: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    try:
        if page_number < 1 or page_number > len(doc):
            return []
        page = doc[page_number - 1]
        page_rect = page.rect

        rects = []
        for snippet_len in [100, 60, 40, 25]:
            snippet = _normalize_snippet(target_text, snippet_len)
            if not snippet.strip():
                continue
            rects = page.search_for(snippet)
            if rects:
                break

        normalized = [
            {
                "x0": r.x0 / page_rect.width,
                "y0": r.y0 / page_rect.height,
                "x1": r.x1 / page_rect.width,
                "y1": r.y1 / page_rect.height,
            }
            for r in rects
        ]
        return normalized
    finally:
        doc.close()
