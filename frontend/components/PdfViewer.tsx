"use client";

import { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { X, ChevronLeft, ChevronRight } from "lucide-react";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

// react-pdf butuh worker pdf.js -- pakai CDN supaya tidak perlu setup
// bundler tambahan. Sesuaikan versi dengan versi pdfjs-dist yang
// terinstall (otomatis mengikuti react-pdf).
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export type BBox = { x0: number; y0: number; x1: number; y1: number };

export type Citation = {
  source_file: string;
  page_number: number;
  chunk_text: string;
  bbox: BBox[];
};

export default function PdfViewer({
  citation,
  onClose,
}: {
  citation: Citation;
  onClose: () => void;
}) {
  const [currentPage, setCurrentPage] = useState(citation.page_number);
  const [numPages, setNumPages] = useState(0);
  const [pageWidth] = useState(700);

  const filename = citation.source_file.split("/").pop();
  const fileUrl = `${API_BASE}/documents/file/${filename}`;

  // highlight cuma ditampilkan kalau kita sedang di halaman sumber sitasi
  const showHighlight = currentPage === citation.page_number && citation.bbox.length > 0;

  return (
    <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b shrink-0">
          <div className="text-sm">
            <div className="font-medium text-slate-900">{filename}</div>
            <div className="text-xs text-slate-500">Halaman {currentPage} dari {numPages || "…"}</div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={20} />
          </button>
        </div>

        {/* Nav */}
        <div className="flex items-center justify-center gap-3 py-2 border-b shrink-0 bg-slate-50">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage <= 1}
            className="p-1.5 rounded hover:bg-slate-200 disabled:opacity-30"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-xs text-slate-600">Hal. {currentPage}</span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(numPages, p + 1))}
            disabled={currentPage >= numPages}
            className="p-1.5 rounded hover:bg-slate-200 disabled:opacity-30"
          >
            <ChevronRight size={16} />
          </button>
          {citation.page_number !== currentPage && (
            <button
              onClick={() => setCurrentPage(citation.page_number)}
              className="text-xs text-blue-600 underline ml-2"
            >
              Kembali ke halaman sumber ({citation.page_number})
            </button>
          )}
        </div>

        {/* PDF render area */}
        <div className="flex-1 overflow-y-auto flex justify-center bg-slate-100 p-4">
          <div className="relative inline-block shadow" style={{ width: pageWidth }}>
            <Document
              file={fileUrl}
              onLoadSuccess={({ numPages }) => setNumPages(numPages)}
              loading={<div className="text-sm text-slate-500 p-8">Memuat dokumen...</div>}
              error={<div className="text-sm text-red-500 p-8">Gagal memuat PDF.</div>}
            >
              <Page pageNumber={currentPage} width={pageWidth} renderTextLayer={false} renderAnnotationLayer={false} />
            </Document>

            {/* Overlay highlight -- bbox sudah ternormalisasi 0-1, jadi
                cukup pakai persentase, tidak perlu tahu resolusi asli */}
            {showHighlight &&
              citation.bbox.map((b, i) => (
                <div
                  key={i}
                  className="absolute bg-yellow-300/50 border border-yellow-500/70 pointer-events-none"
                  style={{
                    left: `${b.x0 * 100}%`,
                    top: `${b.y0 * 100}%`,
                    width: `${(b.x1 - b.x0) * 100}%`,
                    height: `${(b.y1 - b.y0) * 100}%`,
                  }}
                />
              ))}
          </div>
        </div>

        {!citation.bbox.length && currentPage === citation.page_number && (
          <div className="px-4 py-2 text-xs text-amber-600 bg-amber-50 border-t shrink-0">
            Lokasi highlight tidak dapat ditentukan otomatis untuk halaman ini
            (kemungkinan hasil OCR) — tapi Anda tetap diarahkan ke halaman yang benar.
          </div>
        )}
      </div>
    </div>
  );
}
