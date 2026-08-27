import io
import os
import pytest


@pytest.fixture(autouse=True)
def _cleanup_uploaded_test_files():
    """
    Endpoint /admin/upload menulis ke settings.data_dir (folder data
    PROYEK ASLI, bukan tmp_path terisolasi) karena data_dir adalah
    computed property berbasis base_dir, bukan field yang gampang
    di-monkeypatch. Fixture ini membersihkan file yang dibuat test
    upload supaya tidak mengotori data/raw_pdfs/ proyek sungguhan.
    """
    yield
    from app.config import settings
    raw_dir = os.path.join(settings.data_dir, "raw_pdfs")
    for fname in ["dokumen_asli.pdf", "menyamar.pdf", "dokumen.txt"]:
        path = os.path.join(raw_dir, fname)
        if os.path.isfile(path):
            os.remove(path)


def _register_and_login(client, username: str) -> str:
    client.post("/auth/register", json={
        "email": f"{username}@student.uny.ac.id",
        "username": username,
        "password": "rahasia123",
        "full_name": username.title(),
    })
    response = client.post("/auth/login", json={"identifier": username, "password": "rahasia123"})
    return response.json()["access_token"]


def test_history_delete_only_own_entry(client, monkeypatch):
    """
    Test IDOR (Insecure Direct Object Reference): mahasiswa A tidak
    boleh bisa hapus riwayat mahasiswa B walau tahu/menebak entry_id-nya.
    """
    from app.history.chat_history import save_history_if_logged_in

    token_a = _register_and_login(client, "user_a")
    token_b = _register_and_login(client, "user_b")

    # Simpan satu riwayat untuk user_a secara langsung (bypass endpoint
    # /chat yang butuh Ollama sungguhan -- di luar cakupan test ini)
    import app.history.chat_history as ch
    db_check = ch.SessionLocal()
    from sqlalchemy import text
    user_a_id = db_check.execute(text("SELECT id FROM users WHERE username='user_a'")).scalar()
    db_check.close()

    save_history_if_logged_in(user_a_id, "Pertanyaan A", "Jawaban A", "standard+e5_small")

    history_a = client.get("/history", headers={"Authorization": f"Bearer {token_a}"}).json()
    entry_id = history_a["items"][0]["id"]

    # user_b coba hapus riwayat milik user_a -- HARUS gagal
    response = client.delete(f"/history/{entry_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert response.status_code == 404, "user_b seharusnya TIDAK BISA hapus riwayat milik user_a"

    # user_a hapus riwayatnya sendiri -- HARUS berhasil
    response_own = client.delete(f"/history/{entry_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert response_own.status_code == 200


def test_history_pagination_respects_page_size(client):
    from app.history.chat_history import save_history_if_logged_in
    import app.history.chat_history as ch
    from sqlalchemy import text

    token = _register_and_login(client, "many_chats_user")
    db_check = ch.SessionLocal()
    user_id = db_check.execute(text("SELECT id FROM users WHERE username='many_chats_user'")).scalar()
    db_check.close()

    for i in range(5):
        save_history_if_logged_in(user_id, f"Pertanyaan {i}", f"Jawaban {i}", "standard+e5_small")

    response = client.get("/history?page=1&page_size=2", headers={"Authorization": f"Bearer {token}"})
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total_items"] == 5
    assert body["total_pages"] == 3


def test_upload_rejects_non_pdf_extension(client):
    token = _register_and_login(client, "admin_upload_test")
    import sqlite3
    # promosikan manual (pola sama seperti test_rbac.py)
    import app.auth.models as auth_models
    conn = sqlite3.connect(str(auth_models.engine.url).replace("sqlite:///", ""))
    conn.execute("UPDATE users SET role='admin' WHERE username='admin_upload_test'")
    conn.commit()
    conn.close()

    fake_file = io.BytesIO(b"ini bukan PDF sama sekali")
    response = client.post(
        "/admin/upload",
        files={"file": ("dokumen.txt", fake_file, "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "ekstensi" in response.json()["detail"].lower()


def test_upload_rejects_fake_pdf_with_wrong_magic_bytes(client):
    """File di-rename jadi .pdf tapi isinya bukan PDF asli -- harus tetap ditolak."""
    token = _register_and_login(client, "admin_upload_test2")
    import sqlite3
    import app.auth.models as auth_models
    conn = sqlite3.connect(str(auth_models.engine.url).replace("sqlite:///", ""))
    conn.execute("UPDATE users SET role='admin' WHERE username='admin_upload_test2'")
    conn.commit()
    conn.close()

    fake_pdf = io.BytesIO(b"MZ\x90\x00ini sebenarnya file executable, bukan PDF")
    response = client.post(
        "/admin/upload",
        files={"file": ("menyamar.pdf", fake_pdf, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "signature" in response.json()["detail"].lower()


def test_upload_accepts_valid_pdf_magic_bytes(client):
    token = _register_and_login(client, "admin_upload_test3")
    import sqlite3
    import app.auth.models as auth_models
    conn = sqlite3.connect(str(auth_models.engine.url).replace("sqlite:///", ""))
    conn.execute("UPDATE users SET role='admin' WHERE username='admin_upload_test3'")
    conn.commit()
    conn.close()

    real_pdf_signature = io.BytesIO(b"%PDF-1.7\n%mock content cukup untuk lolos cek magic bytes")
    response = client.post(
        "/admin/upload",
        files={"file": ("dokumen_asli.pdf", real_pdf_signature, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["filename"] == "dokumen_asli.pdf"
