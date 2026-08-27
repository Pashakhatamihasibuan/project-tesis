"""
Semua endpoint di sini WAJIB lewat require_admin -- mahasiswa biasa
(bahkan yang login) akan dapat 403 kalau mencoba akses endpoint ini.
Ini yang dimaksud "admin panel terpisah" dari sisi backend: secara
teknis dia satu FastAPI app yang sama, tapi rutenya diproteksi role,
dan di sisi frontend rute ini tidak pernah di-link dari navigasi
aplikasi mahasiswa (lihat admin-frontend/, aplikasi Next.js terpisah).
"""
import hashlib
import logging
import os
import shutil

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from app.auth.rbac_middleware import require_admin
from app.auth.models import User
from app.config import settings
from app.ingestion.chunker import chunk_pdf
from app.rag.pipeline_factory import get_embedder
from app.api.chat import _store_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

ALLOWED_PDF_MAGIC_BYTES = b"%PDF-"  # signature PDF asli (bukan cuma cek ekstensi nama file)


def _raw_dir() -> str:
    path = os.path.join(settings.data_dir, "raw_pdfs")
    os.makedirs(path, exist_ok=True)
    return path


@router.post("/upload")
async def upload_official_document(
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
):
    """
    Validasi TIGA lapis sebelum file diterima:
    1. Ekstensi nama file (.pdf) -- validasi paling lemah, gampang dipalsukan
    2. Ukuran file <= max_upload_size_mb
    3. Magic bytes (isi 5 byte pertama file HARUS "%PDF-") -- ini yang
       benar-benar membuktikan file berisi PDF sungguhan, bukan file
       .exe/.zip yang sekadar di-rename jadi .pdf.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Hanya file berekstensi .pdf yang diterima.")

    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Ukuran file {len(content) / (1024*1024):.1f} MB melebihi batas maksimal {settings.max_upload_size_mb} MB.",
        )

    if not content.startswith(ALLOWED_PDF_MAGIC_BYTES):
        raise HTTPException(
            status_code=400,
            detail="File tidak dikenali sebagai PDF asli (signature file tidak sesuai), "
                   "meski ekstensinya .pdf. Kemungkinan file rusak atau di-rename dari format lain.",
        )

    dest_path = os.path.join(_raw_dir(), file.filename)
    if os.path.exists(dest_path):
        raise HTTPException(
            status_code=409,
            detail=f"Dokumen '{file.filename}' sudah ada. Hapus dulu via DELETE /admin/documents/{{filename}} kalau ingin mengganti.",
        )

    with open(dest_path, "wb") as f:
        f.write(content)

    logger.info("Dokumen diupload: %s (%.1f MB) oleh %s", file.filename, len(content) / (1024*1024), admin.username)
    return {
        "status": "uploaded",
        "filename": file.filename,
        "size_mb": round(len(content) / (1024 * 1024), 2),
        "uploaded_by": admin.username,
    }


@router.get("/documents")
def list_official_documents(admin: User = Depends(require_admin)):
    """Daftar dokumen resmi yang sudah diupload -- sebelumnya admin
    tidak punya cara melihat apa saja yang sudah ada tanpa akses filesystem
    langsung."""
    raw_dir = _raw_dir()
    documents = []
    for filename in sorted(os.listdir(raw_dir)):
        if not filename.lower().endswith(".pdf"):
            continue
        path = os.path.join(raw_dir, filename)
        stat = os.stat(path)
        documents.append({
            "filename": filename,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified_at": stat.st_mtime,
        })
    return {"documents": documents, "total": len(documents)}


@router.delete("/documents/{filename}")
def delete_official_document(filename: str, admin: User = Depends(require_admin)):
    safe_filename = os.path.basename(filename)  # cegah path traversal, sama seperti api/documents.py
    path = os.path.join(_raw_dir(), safe_filename)

    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan.")

    os.remove(path)
    logger.info("Dokumen dihapus: %s oleh %s", safe_filename, admin.username)
    return {
        "status": "deleted",
        "filename": safe_filename,
        "note": "Index BELUM diperbarui otomatis -- panggil POST /admin/rebuild-index "
                "supaya chunk dari dokumen ini juga hilang dari hasil pencarian.",
    }


def _deduplicate_across_documents(all_chunks: list) -> list:
    """
    Dedup LINTAS dokumen (beda dari dedup dalam chunker.py yang hanya
    lintas-halaman DALAM satu PDF). Berguna kalau admin upload ulang
    dokumen dengan isi tumpang tindih (misal revisi peraturan yang
    sebagian pasalnya sama persis dengan versi lama yang belum dihapus).
    """
    seen_hashes = set()
    deduplicated = []
    duplicate_count = 0

    for chunk in all_chunks:
        text_hash = hashlib.md5(chunk.text.encode("utf-8")).hexdigest()
        if text_hash in seen_hashes:
            duplicate_count += 1
            continue
        seen_hashes.add(text_hash)
        deduplicated.append(chunk)

    if duplicate_count > 0:
        logger.info("Dedup lintas dokumen: %d chunk duplikat dihapus dari %d total.", duplicate_count, len(all_chunks))

    return deduplicated


@router.post("/rebuild-index")
async def rebuild_index(
    use_dummy_embedder: bool = False,
    admin: User = Depends(require_admin),
):
    """
    Proses ulang SEMUA dokumen di data/raw_pdfs/ untuk ketiga model
    embedding sekaligus. use_dummy_embedder=True untuk testing cepat
    tanpa perlu download model dari HuggingFace.
    """
    raw_dir = _raw_dir()
    pdf_files = [
        os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.lower().endswith(".pdf")
    ]

    all_chunks = []
    for pdf_path in pdf_files:
        all_chunks.extend(chunk_pdf(pdf_path))

    chunks_before_dedup = len(all_chunks)
    all_chunks = _deduplicate_across_documents(all_chunks)

    for embedding_key in settings.embedding_keys:
        embedder = get_embedder(embedding_key, use_dummy=use_dummy_embedder)
        _store_manager.build_index_for_model(all_chunks, embedder)

    return {
        "status": "rebuilt",
        "total_documents": len(pdf_files),
        "total_chunks": len(all_chunks),
        "duplicate_chunks_removed": chunks_before_dedup - len(all_chunks),
        "models_indexed": settings.embedding_keys,
        "triggered_by": admin.username,
    }
