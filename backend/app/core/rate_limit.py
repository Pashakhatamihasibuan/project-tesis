"""
Rate limiting berbasis IP address, pakai slowapi (wrapper limits untuk
FastAPI). Dipasang di endpoint yang rawan disalahgunakan:

- /chat: tanpa limit, satu orang bisa spam ratusan request ke LLM lokal
  (mahal secara komputasi, bisa bikin server tidak responsif untuk
  pengguna lain).
- /auth/login: tanpa limit, rawan brute-force password.
- /auth/register: tanpa limit, rawan pembuatan akun massal (spam).

Limit disimpan in-memory (default slowapi) -- cukup untuk skala
deployment tesis (single-instance server). Kalau nanti sistem
di-deploy multi-instance/load-balanced, storage in-memory perlu
diganti ke Redis (limits mendukung ini via storage_uri) supaya limit
konsisten lintas instance.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
