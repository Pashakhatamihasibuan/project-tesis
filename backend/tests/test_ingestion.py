import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import fitz


@pytest.fixture(scope="module")
def sample_pdf(tmp_path_factory):
    """Buat PDF contoh sekali per module test, bukan per fungsi (lebih cepat)."""
    tmp_dir = tmp_path_factory.mktemp("pdfs")
    pdf_path = os.path.join(tmp_dir, "contoh.pdf")

    doc = fitz.open()
    page = doc.new_page()
    text = (
        "BAB III\nKETENTUAN AKADEMIK\n\n"
        "Pasal 10\nMahasiswa program Magister wajib menempuh sekurang-kurangnya "
        "36 (tiga puluh enam) SKS untuk dapat dinyatakan lulus, termasuk tesis.\n\n"
        "Pasal 11\nMasa studi program Magister paling lama 4 (empat) semester.\n"
    )
    # insert_textbox (bukan insert_text) supaya teks word-wrap otomatis
    # dalam batas rect halaman -- insert_text tidak wrap dan bisa
    # memotong kalimat diam-diam kalau lebih lebar dari halaman.
    page.insert_textbox(fitz.Rect(50, 50, 500, 700), text, fontsize=11)
    doc.save(pdf_path)
    doc.close()
    return pdf_path


def test_chunking_preserves_pasal_boundaries(sample_pdf):
    """
    Test paling penting untuk validitas eksperimen: strategi chunking
    HARUS menjaga satu Pasal jadi satu chunk utuh, tidak terpotong di
    tengah -- ini klaim metodologis eksplisit di Bab III tesis.
    """
    from app.ingestion.chunker import chunk_pdf

    chunks = chunk_pdf(sample_pdf)
    pasal_chunks = [c for c in chunks if c.content_type == "pasal" and "Pasal 10" in c.text]

    assert len(pasal_chunks) == 1, "Pasal 10 seharusnya jadi satu chunk utuh, bukan terpecah"
    assert "36" in pasal_chunks[0].text
    assert "tesis" in pasal_chunks[0].text


def test_chunking_deduplicates_identical_text(sample_pdf):
    from app.ingestion.chunker import chunk_pdf

    chunks = chunk_pdf(sample_pdf)
    texts = [c.text for c in chunks]
    assert len(texts) == len(set(texts)), "Ditemukan chunk dengan teks identik -- dedup gagal"


def test_structure_parser_splits_by_pasal():
    from app.ingestion.structure_parser import split_by_legal_structure

    text = "Pasal 1\nIsi pasal satu.\nPasal 2\nIsi pasal dua."
    sections = split_by_legal_structure(text)

    assert len(sections) == 2
    assert sections[0].heading == "Pasal 1"
    assert sections[1].heading == "Pasal 2"
    assert "Isi pasal dua" in sections[1].text
    assert "Isi pasal dua" not in sections[0].text  # tidak bocor ke section sebelumnya


def test_structure_parser_fallback_to_prosa_without_pasal():
    from app.ingestion.structure_parser import split_by_legal_structure

    text = "Ini paragraf biasa tanpa struktur Pasal atau BAB sama sekali."
    sections = split_by_legal_structure(text)

    assert len(sections) == 1
    assert sections[0].section_type == "prosa"
