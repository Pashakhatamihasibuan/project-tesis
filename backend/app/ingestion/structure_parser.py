"""
Structure-aware splitting untuk dokumen regulasi akademik.

Alih-alih langsung memotong per 512 karakter (yang bisa memotong satu
Pasal jadi dua chunk berbeda), kita split dulu berdasarkan struktur
dokumen resmi Indonesia: BAB, Pasal, Ayat. Baru bagian yang masih
kepanjangan di-fallback ke recursive character splitting.
"""
import re
from dataclasses import dataclass


@dataclass
class StructuralSection:
    heading: str          # misal "Pasal 12" atau "BAB III"
    text: str             # isi lengkap section ini
    section_type: str     # "pasal" | "bab" | "prosa"


# Pola umum dokumen regulasi akademik Indonesia
_PASAL_PATTERN = re.compile(r"(?=\bPasal\s+\d+\b)")
_BAB_PATTERN = re.compile(r"(?=\bBAB\s+[IVXLCDM]+\b)")


def split_by_legal_structure(text: str) -> list[StructuralSection]:
    """
    Coba split berdasarkan 'Pasal N' dulu (paling granular & paling
    sering dirujuk mahasiswa, misal "Pasal 12 ayat 3"). Kalau dokumen
    tidak mengandung pola Pasal sama sekali, coba split per BAB.
    Kalau keduanya tidak ada, treat sebagai satu section prosa biasa.
    """
    pasal_splits = _PASAL_PATTERN.split(text)
    pasal_splits = [s.strip() for s in pasal_splits if s.strip()]

    if len(pasal_splits) > 1:
        sections = []
        for chunk in pasal_splits:
            heading_match = re.match(r"(Pasal\s+\d+)", chunk)
            heading = heading_match.group(1) if heading_match else "Pasal (tanpa nomor)"
            sections.append(StructuralSection(heading=heading, text=chunk, section_type="pasal"))
        return sections

    bab_splits = _BAB_PATTERN.split(text)
    bab_splits = [s.strip() for s in bab_splits if s.strip()]
    if len(bab_splits) > 1:
        sections = []
        for chunk in bab_splits:
            heading_match = re.match(r"(BAB\s+[IVXLCDM]+)", chunk)
            heading = heading_match.group(1) if heading_match else "BAB (tanpa nomor)"
            sections.append(StructuralSection(heading=heading, text=chunk, section_type="bab"))
        return sections

    return [StructuralSection(heading="", text=text, section_type="prosa")]
