"""
Prinsip penting: riwayat HANYA ditulis kalau ada user login (user_id
valid). Untuk guest, fungsi ini tidak pernah dipanggil sama sekali --
bukan disimpan lalu dihapus, tapi memang tidak pernah tersentuh
database. Ini konsisten dengan alur yang didemonstrasikan di prototipe
frontend sebelumnya.
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

from app.config import settings  # simpan di DB yang sama demi kesederhanaan

Base = declarative_base()


class ChatHistoryEntry(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)  # WAJIB ada, tidak nullable
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    configuration = Column(String)  # misal "standard+e5_small"
    created_at = Column(DateTime, default=datetime.utcnow)


engine = create_engine(f"sqlite:///{settings.auth_db}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def init_history_db():
    Base.metadata.create_all(engine)


def save_history_if_logged_in(user_id: int | None, question: str, answer: str, configuration: str):
    if user_id is None:
        return  # GUEST -- tidak disimpan, titik.

    db = SessionLocal()
    try:
        entry = ChatHistoryEntry(
            user_id=user_id, question=question, answer=answer, configuration=configuration
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()


def get_history_for_user(user_id: int, page: int = 1, page_size: int = 20) -> dict:
    """
    Pagination -- tanpa ini, riwayat chat seorang user yang sudah ratusan
    entri akan diambil SEKALIGUS setiap kali buka halaman Riwayat Chat,
    membebani query DB dan payload response tanpa perlu (user hampir
    tidak pernah scroll sampai entri ke-200).
    """
    db = SessionLocal()
    try:
        query = db.query(ChatHistoryEntry).filter(ChatHistoryEntry.user_id == user_id)
        total = query.count()

        offset = (page - 1) * page_size
        rows = query.order_by(ChatHistoryEntry.created_at.desc()).offset(offset).limit(page_size).all()

        return {
            "items": [
                {
                    "id": r.id,
                    "question": r.question,
                    "answer": r.answer,
                    "configuration": r.configuration,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows
            ],
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }
    finally:
        db.close()


def delete_history_entry(user_id: int, entry_id: int) -> bool:
    """
    Hapus SATU entri riwayat. Verifikasi entry_id benar-benar milik
    user_id yang meminta -- mencegah mahasiswa A menghapus riwayat
    mahasiswa B hanya dengan menebak-nebak id (IDOR/Insecure Direct
    Object Reference, celah keamanan umum kalau ownership tidak dicek).
    Return True kalau berhasil dihapus, False kalau entri tidak
    ditemukan/bukan milik user ini.
    """
    db = SessionLocal()
    try:
        entry = db.query(ChatHistoryEntry).filter(
            ChatHistoryEntry.id == entry_id,
            ChatHistoryEntry.user_id == user_id,
        ).first()
        if not entry:
            return False
        db.delete(entry)
        db.commit()
        return True
    finally:
        db.close()


def get_recent_turns_for_context(user_id: int, limit: int = 3) -> list[dict]:
    """
    Ambil `limit` giliran percakapan TERAKHIR (bukan seluruh riwayat)
    untuk dipakai sebagai konteks multi-turn di prompt LLM. Dibatasi
    supaya prompt tidak membengkak tanpa batas seiring panjangnya
    riwayat chat seorang user -- lihat settings.max_history_turns.
    Diurutkan dari LAMA ke BARU (kebalikan dari get_history_for_user)
    supaya urutan kronologis pas saat ditempel jadi konteks prompt.
    """
    db = SessionLocal()
    try:
        rows = (
            db.query(ChatHistoryEntry)
            .filter(ChatHistoryEntry.user_id == user_id)
            .order_by(ChatHistoryEntry.created_at.desc())
            .limit(limit)
            .all()
        )
        rows.reverse()
        return [{"question": r.question, "answer": r.answer} for r in rows]
    finally:
        db.close()
