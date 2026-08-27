"""
TurboVec hanya menyimpan vektor terkompresi + ID -- tidak menyimpan teks
atau metadata. doc_store.py ini adalah lapisan pelengkap: SQLite yang
memetakan chunk_id (uint64, dipakai sebagai ID di TurboVec) ke teks asli,
sumber dokumen, halaman, dan tipe konten (pasal/tabel/prosa).

Ini juga yang dipakai fitur "klik sitasi -> buka halaman -> highlight".
"""
import sqlite3
import json
import hashlib


def chunk_id_to_uint64(chunk_id: str) -> int:
    """TurboVec butuh ID uint64. chunk_id kita berupa hex string (dari
    chunker.py), jadi kita hash ulang jadi integer deterministik.

    Dibatasi ke 62 bit (bukan 64 penuh) supaya tetap muat di kolom
    SQLite INTEGER (signed 64-bit, max ~9.2e18) sekaligus tetap valid
    sebagai uint64 untuk TurboVec."""
    h = hashlib.sha256(chunk_id.encode("utf-8")).hexdigest()
    return int(h[:16], 16) & 0x3FFFFFFFFFFFFFFF  # mask ke 62 bit


class DocStore:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                vector_id INTEGER PRIMARY KEY,
                chunk_id TEXT UNIQUE NOT NULL,
                text TEXT NOT NULL,
                source_file TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                content_type TEXT NOT NULL,
                embedding_model TEXT NOT NULL,
                metadata_json TEXT
            )
            """
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_embedding_model ON chunks(embedding_model)"
        )
        self.conn.commit()

    def insert_chunk(self, chunk, embedding_model: str) -> int:
        vector_id = chunk_id_to_uint64(chunk.chunk_id)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO chunks
            (vector_id, chunk_id, text, source_file, page_number, content_type, embedding_model, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vector_id,
                chunk.chunk_id,
                chunk.text,
                chunk.source_file,
                chunk.page_number,
                chunk.content_type,
                embedding_model,
                json.dumps(chunk.metadata),
            ),
        )
        self.conn.commit()
        return vector_id

    def get_by_vector_id(self, vector_id: int, embedding_model: str) -> dict | None:
        cur = self.conn.execute(
            "SELECT chunk_id, text, source_file, page_number, content_type, metadata_json "
            "FROM chunks WHERE vector_id = ? AND embedding_model = ?",
            (vector_id, embedding_model),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "chunk_id": row[0],
            "text": row[1],
            "source_file": row[2],
            "page_number": row[3],
            "content_type": row[4],
            "metadata": json.loads(row[5]) if row[5] else {},
        }

    def get_all_texts(self, embedding_model: str) -> list[dict]:
        """Dipakai untuk membangun index BM25 (butuh semua teks + id)."""
        cur = self.conn.execute(
            "SELECT vector_id, text FROM chunks WHERE embedding_model = ?",
            (embedding_model,),
        )
        return [{"vector_id": r[0], "text": r[1]} for r in cur.fetchall()]
