"""
OCR fallback untuk halaman PDF yang tidak punya text layer (hasil scan).

CATATAN INSTALASI: butuh binary `tesseract-ocr` + language pack `ind`
terinstall di OS (bukan cuma pip install pytesseract). Di Ubuntu/Debian:

    sudo apt-get install tesseract-ocr tesseract-ocr-ind

Kalau tesseract belum ada di sistem, fungsi ini akan raise RuntimeError
dengan pesan yang jelas -- bukan gagal diam-diam.
"""
import io

from app.config import settings
from app.ingestion.pdf_loader import get_page_pixmap


def ocr_page(pdf_path: str, page_number: int) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as e:
        raise RuntimeError(
            "pytesseract/Pillow belum terinstall. Jalankan: pip install pytesseract Pillow"
        ) from e

    pix = get_page_pixmap(pdf_path, page_number, dpi=settings.ocr_dpi)
    img_bytes = pix.tobytes("png")
    image = Image.open(io.BytesIO(img_bytes))

    try:
        text = pytesseract.image_to_string(image, lang=settings.ocr_lang)
    except pytesseract.TesseractNotFoundError as e:
        raise RuntimeError(
            "Binary tesseract-ocr tidak ditemukan di sistem. "
            "Install dengan: sudo apt-get install tesseract-ocr tesseract-ocr-ind"
        ) from e

    return text.strip()


def ocr_pages_needed(pdf_path: str, pages: list) -> dict[int, str]:
    """
    Jalankan OCR hanya untuk halaman yang ditandai needs_ocr=True.
    Return dict {page_number: ocr_text}.
    """
    results = {}
    for p in pages:
        if p.needs_ocr:
            results[p.page_number] = ocr_page(pdf_path, p.page_number)
    return results
