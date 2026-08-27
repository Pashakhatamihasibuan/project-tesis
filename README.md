# AkademiQ — Chatbot Akademik S2 PTEI Berbasis RAG

Proyek ini sudah **teruji jalan end-to-end** (bukan cuma outline) untuk bagian:
ingestion (OCR-aware + structure-aware chunking) → indexing (TurboVec + BM25) →
hybrid retrieval → FastAPI dengan auth guest/login + RBAC admin.

Bagian yang butuh setup tambahan di mesin kamu sendiri (tidak bisa dites di
sandbox pembuatan proyek ini karena keterbatasan jaringan): **Ollama** (LLM),
**model embedding asli dari HuggingFace**, **Tesseract OCR**, dan **npm install**
untuk frontend.

## Status komponen

| Komponen | Status |
|---|---|
| Ingestion (PDF, OCR fallback, tabel, Pasal/BAB) | ✅ Teruji jalan |
| Chunking (structure-aware + recursive fallback + dedup) | ✅ Teruji jalan |
| TurboVec index (add/search) | ✅ Teruji jalan |
| BM25 + Hybrid retrieval (RRF) | ✅ Teruji jalan |
| Auth (register/login/JWT) | ✅ Teruji jalan |
| RBAC (admin vs mahasiswa vs guest) | ✅ Teruji jalan (403/401 terverifikasi) |
| Riwayat chat (hanya tersimpan jika login) | ✅ Teruji jalan |
| Endpoint admin (upload, rebuild index) | ✅ Teruji jalan (dengan dummy embedder) |
| Embedding asli (E5/MPNet/LaBSE) | ⚠️ Kode sudah ada, butuh koneksi internet ke huggingface.co saat pertama load |
| LLM (Aya 23 8B via Ollama) | ⚠️ Kode sudah ada, butuh Ollama terinstall & jalan di mesin kamu |
| OCR (Tesseract) | ⚠️ Kode sudah ada, butuh binary `tesseract-ocr` terinstall di OS |
| Cross-encoder re-ranking | ⚠️ Kode sudah ada, butuh koneksi internet ke huggingface.co |
| Frontend Next.js | ✅ Kode lengkap, belum di-`npm install`/jalankan (lakukan di mesin kamu) |

## Setup di mesin kamu (Juli, minggu pertama)

### 1. Backend

```bash
cd backend
pip install -r requirements.txt --break-system-packages

# OCR (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-ind

# Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull aya:8b
ollama serve &

# Jalankan server
python3 -m uvicorn app.main:app --reload --port 8000
```

Pertama kali endpoint `/admin/rebuild-index` dipanggil dengan
`use_dummy_embedder=false`, `sentence-transformers` akan otomatis
mengunduh bobot 3 model (E5-small, MPNet, LaBSE) dan cross-encoder dari
HuggingFace — pastikan ada koneksi internet saat itu. Setelah itu,
model ter-cache lokal (`~/.cache/huggingface`) dan bisa dipakai offline
seterusnya, konsisten dengan prinsip "local RAG" di proposal.

### 2. Frontend mahasiswa

```bash
cd frontend
npm install
npm run dev   # jalan di http://localhost:3000
```

### 3. Admin frontend (aplikasi terpisah, port beda)

```bash
cd admin-frontend
npm install
npm run dev   # jalan di http://localhost:3001
```

## Cara promosikan user jadi admin

Role admin **sengaja tidak bisa didaftarkan lewat endpoint publik**.
Setelah user register biasa, promosikan manual lewat database:

```bash
cd backend
python3 -c "
import sqlite3
conn = sqlite3.connect('auth.sqlite3')
conn.execute(\"UPDATE users SET role='admin' WHERE username='USERNAME_KAMU'\")
conn.commit()
"
```

## Alur kerja membangun index dokumen resmi

1. Taruh PDF dokumen akademik UNY di `data/raw_pdfs/`.
2. Login sebagai admin, dapatkan token.
3. Panggil `POST /admin/rebuild-index` dengan token admin.
4. Sistem otomatis: load PDF → deteksi halaman perlu OCR → ekstrak tabel →
   split per Pasal/BAB → fallback recursive split → dedup → embed dengan
   3 model → index ke TurboVec + BM25.

## Menjalankan evaluasi RAGAS (9 konfigurasi)

Script `scripts/build_official_index.py` dan modul `evaluation/` dari
outline sebelumnya belum ditulis penuh di iterasi ini — prioritas
iterasi ini adalah memvalidasi **fondasi pipeline** (ingestion →
retrieval → auth) benar-benar jalan. Modul evaluasi RAGAS bisa
ditambahkan berikutnya, tinggal panggil `get_pipeline()` dari
`rag/pipeline_factory.py` untuk masing-masing dari 9 kombinasi.

## Catatan penting soal TurboVec

Wrapper `vectorstore/turbovec_index.py` sudah divalidasi jalan dengan
`turbovec.IdMapIndex` versi yang terinstall dari PyPI saat proyek ini
dibuat. Kalau API TurboVec berubah di versi mendatang (masih library
baru, ~1 bulan rilis), cek ulang signature dengan:

```python
import turbovec
help(turbovec.IdMapIndex)
```

## Struktur folder

Lihat outline lengkap di percakapan sebelumnya — struktur folder pada
proyek ini mengikuti persis outline tersebut.
