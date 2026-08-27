"""
Serving file PDF asli supaya frontend bisa render lewat react-pdf.
Dokumen resmi bisa dibaca semua orang (guest termasuk) -- konsisten
dengan desain "Dokumen" yang publik di mockup, beda dengan endpoint
/admin/* yang khusus upload & rebuild (RBAC admin).
"""
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_public_documents():
    """
    List dokumen resmi untuk DIJELAJAHI mahasiswa/guest (halaman
    Dokumen di frontend) -- beda dari GET /admin/documents yang
    formatnya sama tapi khusus admin (RBAC). Endpoint ini sengaja
    TANPA proteksi RBAC karena melihat daftar dokumen resmi bersifat
    publik (sama seperti bisa buka-buka dokumen fisik di perpustakaan),
    yang diproteksi hanya aksi UPLOAD/DELETE (lihat admin_routes.py).
    """
    raw_dir = os.path.join(settings.data_dir, "raw_pdfs")
    if not os.path.isdir(raw_dir):
        return {"documents": [], "total": 0}

    documents = []
    for filename in sorted(os.listdir(raw_dir)):
        if not filename.lower().endswith(".pdf"):
            continue
        path = os.path.join(raw_dir, filename)
        stat = os.stat(path)
        documents.append({
            "filename": filename,
            "display_name": filename.replace(".pdf", "").replace("_", " ").title(),
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
        })
    return {"documents": documents, "total": len(documents)}


@router.get("/file/{filename}")
def get_document_file(filename: str):
    # cegah path traversal (../../etc/passwd dsb)
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(settings.data_dir, "raw_pdfs", safe_filename)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan.")

    return FileResponse(file_path, media_type="application/pdf", filename=safe_filename)
