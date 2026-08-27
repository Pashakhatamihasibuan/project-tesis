#!/usr/bin/env python3
"""
Bangun index (TurboVec + BM25 + doc_store) dari seluruh PDF di
data/raw_pdfs/, untuk ketiga model embedding sekaligus.

Pemakaian:
    python scripts/build_official_index.py
    python scripts/build_official_index.py --dummy   # testing tanpa HuggingFace

Sebelumnya logic ini nempel di app/api/admin_routes.py (harus lewat
HTTP request + auth admin). Script ini versi standalone untuk dipakai
langsung dari command line saat development/riset, tanpa perlu server
FastAPI menyala.
"""
import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.logging_config import setup_logging
from app.config import settings
from app.ingestion.chunker import chunk_pdf
from app.rag.pipeline_factory import get_embedder
from app.vectorstore.store_manager import StoreManager

setup_logging()
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Bangun index dokumen resmi AkademiQ")
    parser.add_argument(
        "--dummy", action="store_true",
        help="Pakai dummy embedder (testing cepat, tanpa akses HuggingFace)",
    )
    args = parser.parse_args()

    raw_dir = os.path.join(settings.data_dir, "raw_pdfs")
    if not os.path.isdir(raw_dir):
        logger.error("Folder %s tidak ditemukan.", raw_dir)
        sys.exit(1)

    pdf_files = [os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        logger.error("Tidak ada file PDF di %s. Taruh dokumen resmi di sana dulu.", raw_dir)
        sys.exit(1)

    logger.info("Ditemukan %d dokumen PDF.", len(pdf_files))

    all_chunks = []
    for pdf_path in pdf_files:
        logger.info("Memproses: %s", os.path.basename(pdf_path))
        chunks = chunk_pdf(pdf_path)
        logger.info("  -> %d chunk dihasilkan", len(chunks))
        all_chunks.extend(chunks)

    logger.info("Total chunk dari seluruh dokumen: %d", len(all_chunks))

    store_manager = StoreManager()
    for embedding_key in settings.embedding_keys:
        logger.info("Membangun index untuk model embedding: %s", embedding_key)
        embedder = get_embedder(embedding_key, use_dummy=args.dummy)
        store_manager.build_index_for_model(all_chunks, embedder)
        logger.info("  -> index %s selesai (%d vektor)", embedding_key, len(store_manager.get_turbovec_store(embedding_key)))

    logger.info("Selesai. Index tersimpan di %s", settings.index_dir)


if __name__ == "__main__":
    main()
