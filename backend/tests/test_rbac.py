"""
Test RBAC -- ini yang PALING KRITIS di seluruh test suite, karena
kalau ada regresi di sini, mahasiswa biasa bisa dapat akses admin
tanpa terdeteksi sampai ada yang menyalahgunakannya.
"""
import sqlite3


def _register_and_login(client, username: str) -> str:
    client.post("/auth/register", json={
        "email": f"{username}@student.uny.ac.id",
        "username": username,
        "password": "rahasia123",
        "full_name": username.title(),
    })
    response = client.post("/auth/login", json={"identifier": username, "password": "rahasia123"})
    return response.json()["access_token"]


def _promote_to_admin(temp_dbs, username: str):
    """Simulasikan promosi manual via DB, persis prosedur di README."""
    conn = sqlite3.connect(temp_dbs["auth_db"])
    conn.execute("UPDATE users SET role='admin' WHERE username=?", (username,))
    conn.commit()
    conn.close()


def test_mahasiswa_cannot_access_admin_endpoint(client):
    token = _register_and_login(client, "mahasiswa1")
    response = client.post("/admin/rebuild-index", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_guest_cannot_access_history(client):
    response = client.get("/history")
    assert response.status_code == 401


def test_mahasiswa_can_access_own_history(client):
    token = _register_and_login(client, "mahasiswa2")
    response = client.get("/history", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []  # belum pernah chat
    assert body["total_items"] == 0


def test_admin_promotion_takes_effect_immediately_without_relogin(client, temp_dbs):
    """
    Membuktikan perilaku RBAC sesungguhnya: otorisasi selalu mengecek
    `user.role` LANGSUNG dari database saat request masuk, BUKAN dari
    field role yang ter-embed di JWT saat token diterbitkan. Karena
    itu, token lama (diterbitkan SEBELUM promosi) tetap mendapat akses
    admin begitu role di database diubah -- tidak perlu login ulang.
    Ini properti keamanan yang diinginkan (revocation/promotion
    instan), bukan bug.
    """
    token = _register_and_login(client, "calon_admin")

    # Sebelum promosi: token ini (role mahasiswa) harus ditolak
    response_before = client.post(
        "/admin/rebuild-index?use_dummy_embedder=true", headers={"Authorization": f"Bearer {token}"}
    )
    assert response_before.status_code == 403

    _promote_to_admin(temp_dbs, "calon_admin")

    # SETELAH promosi, token YANG SAMA (belum login ulang) langsung
    # dapat akses -- karena diverifikasi ulang ke DB tiap request.
    response_after = client.post(
        "/admin/rebuild-index?use_dummy_embedder=true", headers={"Authorization": f"Bearer {token}"}
    )
    assert response_after.status_code != 403


def test_invalid_token_rejected(client):
    response = client.get("/history", headers={"Authorization": "Bearer token-palsu-asal-asalan"})
    assert response.status_code == 401


def test_missing_bearer_prefix_treated_as_guest(client):
    """
    Header Authorization tanpa prefix 'Bearer ' harus diperlakukan
    sebagai guest (bukan error 500) -- pengecekan defensif di
    rbac_middleware.py yang WAJIB tetap jalan.
    """
    response = client.get("/history", headers={"Authorization": "token-tanpa-bearer-prefix"})
    assert response.status_code == 401  # diperlakukan sebagai guest -> ditolak akses history
