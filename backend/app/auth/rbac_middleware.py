"""
Dua dependency penting:

- get_current_user_optional: dipakai di endpoint chat. Kalau ada token
  valid -> return user (role mahasiswa/admin). Kalau tidak ada token /
  token invalid -> return None (dianggap GUEST, tetap boleh chat, tapi
  riwayat TIDAK disimpan -- lihat history/chat_history.py).

- require_admin: dipakai di semua endpoint /admin/*. Kalau bukan admin
  -> 403 Forbidden. Ini yang memastikan upload dokumen resmi & rebuild
  index tidak bisa diakses mahasiswa biasa, walau tahu URL-nya.

CATATAN DESAIN PENTING (dibuktikan oleh tests/test_rbac.py): role yang
dipakai untuk otorisasi SELALU diambil LANGSUNG dari database saat
request masuk (`user.role`), BUKAN dari field "role" yang ikut
ter-embed di dalam JWT saat token diterbitkan. Konsekuensinya:

1. Promosi admin via database berlaku SEKETIKA pada request berikutnya,
   walau memakai token lama yang diterbitkan sebelum promosi -- TIDAK
   perlu login ulang untuk itu berfungsi (meski login ulang tetap
   praktik yang wajar dilakukan user).
2. Sebaliknya, kalau admin di-demote/dihapus dari database, token yang
   masih berlaku (belum expired) LANGSUNG kehilangan akses juga pada
   request berikutnya -- properti ini bagus untuk revocation instan,
   trade-off-nya adalah satu query DB tambahan tiap request
   terautentikasi (dampak performa dapat diabaikan untuk skala
   penelitian ini).
"""
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.auth.models import get_db, User


def _extract_user_from_token(authorization: str | None, db: Session) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)
    if not payload:
        return None
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    return user


def get_current_user_optional(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    return _extract_user_from_token(authorization, db)


def require_admin(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    user = _extract_user_from_token(authorization, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak: khusus admin.")
    return user


def require_authenticated_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """
    Beda dari get_current_user_optional: dependency ini MEWAJIBKAN
    login (mahasiswa ATAU admin, keduanya boleh), guest ditolak 401.
    Dipakai di endpoint yang perlu identitas user tapi tidak perlu
    role admin spesifik -- misal /auth/refresh, /history/{id} (delete).
    """
    user = _extract_user_from_token(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Autentikasi diperlukan untuk mengakses endpoint ini.")
    return user
