"""
Test rate limiting -- membuktikan limit BENAR-BENAR aktif (bukan
sekadar terpasang di kode tapi tidak berfungsi). Tiap test di file ini
independen soal limiter state karena conftest.py me-reset limiter
sebelum tiap test (lihat catatan di conftest.py `client` fixture).
"""


def test_register_rate_limit_blocks_excessive_requests(client):
    """Limit register: 3/menit (lihat settings.rate_limit_register)."""
    for i in range(3):
        response = client.post("/auth/register", json={
            "email": f"user{i}@test.com",
            "username": f"user{i}",
            "password": "rahasia123",
            "full_name": f"User {i}",
        })
        assert response.status_code == 200, f"Request ke-{i+1} seharusnya masih diizinkan"

    response_4th = client.post("/auth/register", json={
        "email": "user4@test.com",
        "username": "user4",
        "password": "rahasia123",
        "full_name": "User 4",
    })
    assert response_4th.status_code == 429


def test_login_rate_limit_blocks_brute_force_attempts(client):
    """Limit login: 5/menit (lihat settings.rate_limit_login) -- mitigasi brute-force password."""
    client.post("/auth/register", json={
        "email": "bruteforce@test.com", "username": "bfvictim",
        "password": "passwordbenar123", "full_name": "Victim",
    })

    for i in range(5):
        response = client.post("/auth/login", json={"identifier": "bfvictim", "password": "salahterus"})
        assert response.status_code == 401, f"Percobaan ke-{i+1} seharusnya masih diproses (401 salah password)"

    response_6th = client.post("/auth/login", json={"identifier": "bfvictim", "password": "salahterus"})
    assert response_6th.status_code == 429, "Percobaan ke-6 seharusnya diblokir rate limit, bukan diproses lagi"
