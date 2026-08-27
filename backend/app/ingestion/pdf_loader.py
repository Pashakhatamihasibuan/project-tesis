"""
Ekstraksi teks dari PDF menggunakan PyMuPDF (fitz).
Halaman yang hasil ekstraksinya kosong/minim otomatis ditandai untuk
diproses via OCR (lihat ocr_engine.py).
"""
from dataclasses import dataclass, field
import fitz  # PyMuPDF

from app.config import settings


@dataclass
class PageContent:
    page_number: int  # 1-indexed, sesuai yang dilihat manusia
    text: str
    needs_ocr: bool
    source_file: str
    bbox_words: list = field(default_factory=list)  # [(word, x0, y0, x1, y1), ...]


def load_pdf_pages(pdf_path: str) -> list[PageContent]:
    """
    Buka PDF, ekstrak teks native tiap halaman.
    Simpan juga bounding box tiap kata (untuk fitur highlight-on-click nanti).
    """
    doc = fitz.open(pdf_path)
    pages = []

    for i, page in enumerate(doc):
        text = page.get_text().strip()
        needs_ocr = len(text) < settings.ocr_min_text_len

        words = page.get_text("words")  # list of (x0, y0, x1, y1, word, block, line, word_no)
        bbox_words = [(w[4], w[0], w[1], w[2], w[3]) for w in words]

        pages.append(
            PageContent(
                page_number=i + 1,
                text=text,
                needs_ocr=needs_ocr,
                source_file=pdf_path,
                bbox_words=bbox_words,
            )
        )

    doc.close()
    return pages


def get_page_pixmap(pdf_path: str, page_number: int, dpi: int = 300):
    """Ambil gambar halaman (untuk OCR atau untuk preview)."""
    doc = fitz.open(pdf_path)
    page = doc[page_number - 1]
    pix = page.get_pixmap(dpi=dpi)
    doc.close()
    return pix
