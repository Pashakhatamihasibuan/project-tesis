import logging
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.core.logging_config import setup_logging
from app.core.rate_limit import limiter
from app.config import settings
from app.auth.models import init_db
from app.history.chat_history import init_history_db
from app.auth.routes import router as auth_router
from app.api.chat import router as chat_router
from app.api.history_routes import router as history_router
from app.api.admin_routes import router as admin_router
from app.api.documents import router as documents_router

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="AkademiQ API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # frontend & admin-frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    init_history_db()
    logger.info("AkademiQ API startup selesai (level log: %s)", settings.log_level)


app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(history_router)
app.include_router(admin_router)
app.include_router(documents_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "AkademiQ API"}


@app.get("/health")
async def health_check():
    """
    Health check SUNGGUHAN -- benar-benar mengecek dependency kritis,
    bukan cuma balas "ok" tanpa validasi apa pun. Dipakai untuk
    diagnosis cepat ("kenapa chat tidak jalan?") tanpa perlu baca log.
    """
    checks = {}

    # Cek Ollama benar-benar hidup dan bisa dihubungi
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            checks["ollama"] = "ok" if resp.status_code == 200 else f"error (status {resp.status_code})"
    except Exception as e:
        checks["ollama"] = f"unreachable ({type(e).__name__})"

    # Cek DB auth bisa diakses
    try:
        from app.auth.models import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        checks["auth_db"] = "ok"
    except Exception as e:
        checks["auth_db"] = f"error ({type(e).__name__})"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
