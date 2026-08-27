"""
Pembersihan teks: hapus nomor halaman berdiri sendiri, whitespace
berlebih, dan baris header/footer yang berulang persis di banyak halaman
(terdeteksi otomatis, bukan hardcode).
"""
import re
from collections import Counter


_PAGE_NUMBER_LINE = re.compile(r"^\s*\d{1,4}\s*$")


def strip_page_numbers(text: str) -> str:
    lines = text.split("\n")
    cleaned = [ln for ln in lines if not _PAGE_NUMBER_LINE.match(ln)]
    return "\n".join(cleaned)


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def detect_repeated_lines(all_page_texts: list[str], min_occurrence_ratio: float = 0.6) -> set[str]:
    """
    Cari baris yang muncul di >= min_occurrence_ratio dari total halaman
    -- ini biasanya header/footer institusional yang berulang, bukan
    konten substantif.
    """
    line_counter = Counter()
    for text in all_page_texts:
        unique_lines_in_page = set(ln.strip() for ln in text.split("\n") if ln.strip())
        for ln in unique_lines_in_page:
            line_counter[ln] += 1

    threshold = max(2, int(len(all_page_texts) * min_occurrence_ratio))
    return {line for line, count in line_counter.items() if count >= threshold}


def clean_document(all_page_texts: list[str]) -> list[str]:
    repeated = detect_repeated_lines(all_page_texts)
    cleaned_pages = []
    for text in all_page_texts:
        text = strip_page_numbers(text)
        lines = [ln for ln in text.split("\n") if ln.strip() not in repeated]
        text = "\n".join(lines)
        text = normalize_whitespace(text)
        cleaned_pages.append(text)
    return cleaned_pages
