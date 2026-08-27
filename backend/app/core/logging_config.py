"""
Konfigurasi logging terpusat. Dipanggil sekali di app/main.py saat
startup. Semua modul lain cukup `logging.getLogger(__name__)` seperti
biasa -- konfigurasi format/level diatur di sini, bukan berserakan.

LOG_JSON=true menghasilkan output JSON satu baris per log -- format
yang mudah di-ingest tools observability (Langfuse, ELK, dsb) kalau
nanti sistem ini di-deploy lebih serius. Default (False) pakai format
manusiawi untuk development sehari-hari.
"""
import logging
import sys
import json
from datetime import datetime, timezone

from app.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())

    # hindari duplikasi handler kalau setup_logging() terpanggil ulang
    # (misal saat --reload uvicorn me-restart proses)
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%H:%M:%S")
        )
    root_logger.addHandler(handler)

    # uvicorn punya logger sendiri yang cukup berisik di level DEBUG,
    # redam ke INFO supaya tidak menenggelamkan log aplikasi sendiri
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
