"""
Konfigurasi global AkademiQ backend, berbasis pydantic-settings.

Kenapa pydantic-settings (bukan os.getenv manual seperti versi
sebelumnya): validasi tipe otomatis saat startup (contoh: kalau
CHUNK_SIZE_TOKENS di .env diisi "lima ratus" bukan angka, aplikasi
GAGAL START dengan pesan error jelas -- bukan lolos lalu crash diam-diam
di tengah proses embedding). Ini praktik standar untuk service yang
akan dijalankan berulang kali oleh orang lain (dosen penguji, adik
tingkat yang melanjutkan riset ini), bukan cuma di laptop sendiri.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- LLM (Ollama, lokal) ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "aya:8b"
    ollama_timeout_seconds: int = 120

    # --- Chunking ---
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 50

    # --- OCR ---
    ocr_min_text_len: int = 20
    ocr_lang: str = "ind"
    ocr_dpi: int = 300

    # --- Retrieval ---
    top_k_default: int = 5
    rerank_initial_k: int = 15

    # --- Multi-turn context ---
    max_history_turns: int = 3  # jumlah pasangan Q&A terakhir yang dikirim sebagai konteks

    # --- Auth ---
    jwt_secret: str = "ganti-ini-dengan-secret-yang-kuat-di-produksi"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 hari

    # --- Evaluasi RAGAS ---
    ragas_judge_model: str = "aya:8b"          # LLM lokal sebagai "hakim" penilai metrik
    ragas_embedding_model: str = "e5_small"    # embedding TETAP untuk metrik answer_relevancy
    # ^ PENTING secara metodologis: embedding untuk *menilai* jawaban harus
    # konstan di semua 9 konfigurasi. Kalau embedding penilai ikut berubah
    # sesuai embedding yang sedang diuji, hasil metrik jadi bias/circular
    # (embedding menilai dirinya sendiri lebih baik). Lihat evaluation/ragas_runner.py.

    # --- Upload dokumen ---
    max_upload_size_mb: int = 50  # sesuai mockup Bantuan FAQ ("maksimal 50 MB per file")

    # --- Rate limiting ---
    rate_limit_chat: str = "20/minute"       # per IP, cegah spam ke LLM (mahal secara komputasi)
    rate_limit_login: str = "5/minute"       # per IP, cegah brute-force password
    rate_limit_register: str = "3/minute"    # per IP, cegah pembuatan akun massal

    # --- Logging ---
    log_level: str = "INFO"
    log_json: bool = False  # True untuk log format JSON (production/observability tools)

    @property
    def base_dir(self) -> str:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/

    @property
    def data_dir(self) -> str:
        return os.path.join(self.base_dir, "..", "data")

    @property
    def index_dir(self) -> str:
        return os.path.join(self.base_dir, "..", "indices")

    @property
    def doc_store_db(self) -> str:
        return os.path.join(self.base_dir, "doc_store.sqlite3")

    @property
    def auth_db(self) -> str:
        return os.path.join(self.base_dir, "auth.sqlite3")

    @property
    def eval_results_dir(self) -> str:
        return os.path.join(self.base_dir, "evaluation_results")

    # --- Embedding models yang dibandingkan ---
    embedding_models: dict[str, str] = {
        "e5_small": "intfloat/multilingual-e5-small",
        "mpnet": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        "labse": "sentence-transformers/LaBSE",
    }
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    rag_architectures: list[str] = ["standard", "hyde", "rerank"]

    @property
    def embedding_keys(self) -> list[str]:
        return list(self.embedding_models.keys())

    @property
    def all_configurations(self) -> list[dict]:
        return [
            {"architecture": arch, "embedding": emb}
            for arch in self.rag_architectures
            for emb in self.embedding_keys
        ]


@lru_cache
def get_settings() -> Settings:
    """
    Cached supaya .env cuma di-parse sekali per proses, bukan tiap
    kali config diakses. Pola standar FastAPI (lihat dokumentasi resmi
    FastAPI bagian Settings and Environment Variables).
    """
    return Settings()


# Untuk kompatibilitas mundur dengan kode lama yang masih import
# konstanta langsung dari modul ini (misal `from app.config import TOP_K_DEFAULT`).
# Modul baru sebaiknya pakai `get_settings()` langsung.
settings = get_settings()
