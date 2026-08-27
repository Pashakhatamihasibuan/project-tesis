"""
Query expansion sederhana berbasis kamus sinonim informal <-> resmi.
Mahasiswa sering pakai istilah sehari-hari ("matkul", "SKS", "TA") yang
berbeda dari istilah baku dokumen resmi ("mata kuliah", "satuan kredit
semester", "tugas akhir") -- retrieval berbasis embedding semantik
umumnya cukup toleran terhadap ini, tapi BM25 (keyword search) pada
hybrid_search.py sama sekali tidak toleran terhadap variasi kata.

Desain SENGAJA berbasis kamus statis (bukan LLM query rewriting):
lebih cepat (tidak nambah panggilan LLM tambahan seperti HyDE),
predictable, dan cukup untuk domain akademik yang istilahnya terbatas.
Trade-off: tidak menangani variasi yang tidak terdaftar di kamus --
ini keterbatasan yang wajar disebutkan di bab pembahasan.

INI FITUR PELENGKAP (di luar sembilan konfigurasi inti penelitian),
dipakai hanya di mode operasional/chat biasa (use_hybrid=True),
TIDAK dipakai saat evaluasi RAGAS pada sembilan konfigurasi.
"""
import re

# Kamus dasar -- silakan diperluas sesuai istilah yang benar-benar
# muncul di data pertanyaan mahasiswa nyata (idealnya disusun dari
# analisis 150 soal evaluasi + observasi pertanyaan asli saat
# usability testing, bukan ditebak semua di awal).
SYNONYM_MAP: dict[str, list[str]] = {
    "mata kuliah": ["matkul", "mk"],
    "satuan kredit semester": ["sks"],
    "tugas akhir": ["ta", "skripsi", "tesis"],
    "kartu rencana studi": ["krs"],
    "kartu hasil studi": ["khs"],
    "indeks prestasi kumulatif": ["ipk"],
    "indeks prestasi": ["ip"],
    "cuti akademik": ["cuti kuliah", "cuti"],
    "dosen pembimbing": ["dospem"],
    "ujian akhir semester": ["uas"],
    "ujian tengah semester": ["uts"],
    "program studi": ["prodi"],
    "surat keterangan lulus": ["skl"],
}


def _build_reverse_map() -> dict[str, str]:
    """informal -> formal (kebalikan dari SYNONYM_MAP yang formal -> [informal,...])"""
    reverse = {}
    for formal, informal_list in SYNONYM_MAP.items():
        for informal in informal_list:
            reverse[informal.lower()] = formal
    return reverse


_REVERSE_MAP = _build_reverse_map()


def expand_query(query: str) -> str:
    """
    Tambahkan padanan istilah resmi ke query, TANPA menghapus kata
    aslinya -- supaya BM25 tetap bisa match salah satu bentuk (asli
    ATAU padanannya). Contoh:
        "berapa sks matkul RPL" -> "berapa sks matkul RPL satuan kredit semester"
    """
    query_lower = query.lower()
    tokens = re.findall(r"\w+", query_lower)

    additions = []
    for token in tokens:
        if token in _REVERSE_MAP:
            formal = _REVERSE_MAP[token]
            if formal not in query_lower:
                additions.append(formal)

    # cek juga frasa 2 kata (misal "cuti kuliah")
    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]} {tokens[i+1]}"
        if bigram in _REVERSE_MAP:
            formal = _REVERSE_MAP[bigram]
            if formal not in query_lower:
                additions.append(formal)

    if not additions:
        return query

    return f"{query} {' '.join(dict.fromkeys(additions))}"  # dict.fromkeys dedup, jaga urutan
