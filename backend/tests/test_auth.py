"""
Konversi validasi manual (curl) yang sebelumnya dijalankan interaktif
menjadi test otomatis permanen -- bisa dijalankan ulang kapan saja
dengan `pytest tests/test_auth.py -v`.
"""


def test_register_new_user_succeeds(client):
    response = client.post("/auth/register", json={
        "email": "budi@student.uny.ac.id",
        "username": "budi",
        "password": "rahasia123",
        "full_name": "Budi Santoso",
        "institution": "UNY",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "mahasiswa"  # default role, BUKAN admin
    assert "access_token" in data


def test_register_duplicate_email_rejected(client):
    payload = {
        "email": "duplikat@student.uny.ac.id",
        "username": "user1",
        "password": "rahasia123",
        "full_name": "User Satu",
    }
    client.post("/auth/register", json=payload)

    payload["username"] = "user2"  # email sama, username beda
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400


def test_login_with_correct_credentials_succeeds(client):
    client.post("/auth/register", json={
        "email": "login_test@student.uny.ac.id",
        "username": "logintest",
        "password": "passwordbenar",
        "full_name": "Login Test",
    })

    response = client.post("/auth/login", json={
        "identifier": "logintest",
        "password": "passwordbenar",
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_with_wrong_password_rejected(client):
    client.post("/auth/register", json={
        "email": "wrongpass@student.uny.ac.id",
        "username": "wrongpass",
        "password": "passwordbenar",
        "full_name": "Wrong Pass Test",
    })

    response = client.post("/auth/login", json={
        "identifier": "wrongpass",
        "password": "passwordsalah",
    })
    assert response.status_code == 401


def test_login_nonexistent_user_rejected(client):
    response = client.post("/auth/login", json={
        "identifier": "tidak_pernah_daftar",
        "password": "apapun",
    })
    assert response.status_code == 401
