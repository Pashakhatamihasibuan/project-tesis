import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator

from app.auth.models import get_db, User, PasswordResetToken
from app.auth.security import hash_password, verify_password, create_access_token, decode_access_token
from app.auth.rbac_middleware import require_authenticated_user
from app.core.rate_limit import limiter
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

RESET_TOKEN_EXPIRE_MINUTES = 30


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: str
    institution: str | None = None

    @field_validator("password")
    @classmethod
    def password_minimum_length(cls, v: str) -> str:
        # Validasi juga di frontend (UX cepat), tapi backend WAJIB
        # validasi ulang -- frontend bisa dilewati (curl, Postman, dsb).
        if len(v) < 8:
            raise ValueError("Kata sandi minimal 8 karakter.")
        return v


class LoginRequest(BaseModel):
    identifier: str  # email atau username
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_minimum_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Kata sandi minimal 8 karakter.")
        return v


def _hash_token(token: str) -> str:
    # Token reset disimpan dalam bentuk HASH di database (pola sama
    # seperti password) -- kalau database bocor, token mentah tidak
    # bisa dipakai penyerang untuk reset password siapa pun.
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/register")
@limiter.limit(settings.rate_limit_register)
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        (User.email == payload.email) | (User.username == payload.username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email atau username sudah terdaftar.")

    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        institution=payload.institution,
        role="mahasiswa",  # role admin HANYA di-set manual lewat database, tidak lewat endpoint publik
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "role": user.role}


@router.post("/login")
@limiter.limit(settings.rate_limit_login)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.email == payload.identifier) | (User.username == payload.identifier)
    ).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email/username atau kata sandi salah.")

    token = create_access_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "role": user.role}


@router.post("/refresh")
def refresh_token(current_user: User = Depends(require_authenticated_user)):
    """
    Terbitkan token baru dengan masa berlaku diperpanjang, selama token
    LAMA masih valid (belum expired) saat request ini dibuat. User
    tidak perlu login ulang (isi ulang password) untuk memperpanjang
    sesi -- cukup panggil endpoint ini sebelum token lama benar-benar
    kedaluwarsa (misal dipanggil otomatis oleh frontend beberapa saat
    sebelum expiry).

    Catatan desain: ini BUKAN pola refresh-token terpisah yang lebih
    aman (access token pendek + refresh token panjang dengan rotasi) --
    itu peningkatan lanjutan yang wajar disebut di bab keterbatasan.
    Pola sekarang (perpanjang token yang sama) cukup untuk skala tesis,
    tapi kurang ideal untuk produksi sungguhan skala besar.
    """
    new_token = create_access_token(current_user.id, current_user.role)
    return {"access_token": new_token, "token_type": "bearer", "role": current_user.role}


@router.post("/forgot-password")
@limiter.limit(settings.rate_limit_login)  # pakai limit sama ketatnya dengan login
def forgot_password(request: Request, payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    PENTING -- belum ada layanan pengiriman email sungguhan di sistem
    ini (di luar cakupan penelitian). Endpoint ini tetap mengeluarkan
    token reset yang valid dan fungsional, tapi link resetnya di-LOG
    ke konsol server (mode development), BUKAN dikirim ke email
    pengguna. Untuk deployment produksi, ganti bagian logger.info di
    bawah dengan pemanggilan layanan email sungguhan (SendGrid, SMTP,
    dsb) -- integrasinya independen dari sisa logika token yang sudah
    aman (hashed, sekali pakai, kedaluwarsa 30 menit).

    Response SELALU sukses generik, terlepas dari email terdaftar atau
    tidak -- ini praktik keamanan standar (mencegah penyerang memakai
    endpoint ini untuk mengecek email mana saja yang terdaftar di
    sistem / user enumeration attack).
    """
    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        raw_token = secrets.token_urlsafe(32)
        reset_entry = PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
        )
        db.add(reset_entry)
        db.commit()

        # TODO produksi: ganti dengan pengiriman email sungguhan.
        logger.info(
            "[MODE DEV -- belum ada layanan email] Link reset password untuk %s: "
            "http://localhost:3000/reset-password?token=%s (berlaku %d menit)",
            user.email, raw_token, RESET_TOKEN_EXPIRE_MINUTES,
        )

    return {"message": "Jika email terdaftar, tautan reset password telah dikirim."}


@router.post("/reset-password")
@limiter.limit(settings.rate_limit_login)
def reset_password(request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_hash = _hash_token(payload.token)
    reset_entry = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used == 0,
    ).first()

    if not reset_entry or reset_entry.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token reset tidak valid atau sudah kedaluwarsa.")

    user = db.query(User).filter(User.id == reset_entry.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Token reset tidak valid.")

    user.password_hash = hash_password(payload.new_password)
    reset_entry.used = 1  # token sekali pakai -- tidak bisa dipakai ulang
    db.commit()

    return {"message": "Kata sandi berhasil direset. Silakan masuk dengan kata sandi baru."}
