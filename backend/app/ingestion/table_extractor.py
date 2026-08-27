"""
Ekstraksi tabel dari PDF (misal: daftar kode mata kuliah, tabel SKS).
Tabel diperlakukan sebagai chunk ATOMIC -- tidak ikut dipotong oleh
recursive character splitter di chunker.py.
"""
from dataclasses import dataclass
import pdfplumber


@dataclass
class TableChunk:
    content_markdown: str
    page_number: int
    source_file: str
    content_type: str = "table"


def _table_to_markdown(table: list[list]) -> str:
    if not table or not table[0]:
        return ""

    # bersihkan None -> string kosong
    clean = [[(cell or "").strip() for cell in row] for row in table]

    header = clean[0]
    rows = clean[1:]

    md_lines = []
    md_lines.append("| " + " | ".join(header) + " |")
    md_lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row in rows:
        # padding kalau jumlah kolom tidak konsisten antar baris
        padded = row + [""] * (len(header) - len(row))
        md_lines.append("| " + " | ".join(padded[: len(header)]) + " |")

    return "\n".join(md_lines)


def extract_tables(pdf_path: str) -> list[TableChunk]:
    chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table in tables:
                md = _table_to_markdown(table)
                if md.strip():
                    chunks.append(
                        TableChunk(
                            content_markdown=md,
                            page_number=page_idx + 1,
                            source_file=pdf_path,
                        )
                    )
    return chunks
