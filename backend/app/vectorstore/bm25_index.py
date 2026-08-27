"""
Index BM25 -- keyword search klasik yang jadi pelengkap semantic search
(TurboVec). Penting khusus untuk query yang mengandung kode/istilah
persis seperti "Pasal 12" atau "PTI6301", yang kadang kurang match
secara embedding semantik murni.

DIPERKAYA dengan stemming Bahasa Indonesia (Sastrawi): tanpa stemming,
BM25 memperlakukan "mempelajari", "belajar", "dipelajari" sebagai token
yang SAMA SEKALI BERBEDA (tidak ada overlap kata), padahal secara makna
berakar sama. Sastrawi memangkas semua ke bentuk dasar "ajar", sehingga
query "cara belajar efektif" bisa match dokumen yang memakai kata
"mempelajari" atau "pembelajaran" -- meningkatkan recall keyword search
tanpa mengubah semantic search (TurboVec) sama sekali.

CATATAN performa: stemming Sastrawi cukup mahal secara komputasi kalau
dipanggil berulang untuk kata yang sama. StemmerCache di bawah menyimpan
hasil stemming per kata supaya tidak di-stem ulang berkali-kali pada
korpus besar.
"""
import re
from functools import lru_cache
from rank_bm25 import BM25Okapi
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

_stemmer = StemmerFactory().create_stemmer()


@lru_cache(maxsize=50_000)
def _stem_word(word: str) -> str:
    """Cache per kata -- korpus akademik punya banyak kata berulang
    (istilah baku regulasi), cache ini memangkas re-stemming drastis."""
    return _stemmer.stem(word)


def _tokenize(text: str, use_stemming: bool = True) -> list[str]:
    raw_tokens = re.findall(r"\w+", text.lower())
    if not use_stemming:
        return raw_tokens
    return [_stem_word(t) for t in raw_tokens]


class BM25Store:
    def __init__(self, use_stemming: bool = True):
        self.bm25 = None
        self.vector_ids: list[int] = []
        self.use_stemming = use_stemming

    def build(self, documents: list[dict]):
        """
        documents: list of {"vector_id": int, "text": str}
        """
        self.vector_ids = [d["vector_id"] for d in documents]
        tokenized_corpus = [_tokenize(d["text"], self.use_stemming) for d in documents]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query: str, top_k: int = 10) -> list[tuple[int, float]]:
        if self.bm25 is None:
            return []
        tokenized_query = _tokenize(query, self.use_stemming)
        scores = self.bm25.get_scores(tokenized_query)
        ranked = sorted(zip(self.vector_ids, scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]
