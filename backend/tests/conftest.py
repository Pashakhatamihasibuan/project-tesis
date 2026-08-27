"""
Fixture bersama untuk seluruh test suite. `client` pakai FastAPI
TestClient (in-process, tidak perlu server sungguhan jalan) dengan
database SQLite terpisah per sesi test -- supaya test tidak
mencemari/tercemar auth.sqlite3 & doc_store.sqlite3 yang dipakai saat
development manual.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


@pytest.fixture(scope="function")
def temp_dbs(monkeypatch):
    """Arahkan auth_db & doc_store_db ke file sementara per test function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        auth_db_path = os.path.join(tmpdir, "auth_test.sqlite3")
        doc_store_path = os.path.join(tmpdir, "doc_store_test.sqlite3")

        from app.config import get_settings
        get_settings.cache_clear()
        monkeypatch.setenv("JWT_SECRET", "test-secret-key-not-for-production")

        yield {"auth_db": auth_db_path, "doc_store_db": doc_store_path}
        get_settings.cache_clear()


@pytest.fixture(scope="function")
def client(temp_dbs, monkeypatch):
    """
    TestClient FastAPI dengan DB terisolasi. Reinisialisasi engine
    SQLAlchemy supaya benar-benar menunjuk ke DB sementara, bukan
    auth.sqlite3 asli di folder backend/.
    """
    import app.auth.models as auth_models
    import app.history.chat_history as history_models
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    test_engine = create_engine(f"sqlite:///{temp_dbs['auth_db']}", connect_args={"check_same_thread": False})
    auth_models.engine = test_engine
    auth_models.SessionLocal = sessionmaker(bind=test_engine)
    history_models.engine = test_engine
    history_models.SessionLocal = sessionmaker(bind=test_engine)

    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.rate_limit import limiter

    # PENTING: limiter itu singleton module-level yang dipakai bersama
    # SELURUH test dalam satu sesi pytest (app di-import sekali, cache
    # Python module). Tanpa reset ini, test yang register/login berkali-
    # kali (test_auth.py, test_rbac.py, dst) akan saling numpuk hit count
    # dan test belakangan bisa gagal kena 429 Too Many Requests padahal
    # secara logis harusnya lolos -- bukan karena rate limiting-nya salah,
    # tapi karena state-nya bocor antar test yang semestinya terisolasi.
    limiter.reset()

    with TestClient(app) as test_client:
        yield test_client
