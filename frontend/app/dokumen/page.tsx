"use client";

import { Suspense, useEffect, useState, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { FileText, Search, Download } from "lucide-react";
import { fetchPublicDocuments } from "@/lib/api";
import AppShell from "@/components/AppShell";
import PdfViewer, { Citation } from "@/components/PdfViewer";

type DocumentItem = { filename: string; display_name: string; size_mb: number };

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

function DokumenContent() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [viewingDoc, setViewingDoc] = useState<Citation | null>(null);
  const searchParams = useSearchParams();

  useEffect(() => {
    fetchPublicDocuments()
      .then((data) => {
        setDocuments(data.documents);
        const fileParam = searchParams.get("file");
        if (fileParam) {
          const found = data.documents.find((d: DocumentItem) => d.filename === fileParam);
          if (found) {
            setViewingDoc({ source_file: found.filename, page_number: 1, chunk_text: "", bbox: [] });
          }
        }
      })
      .finally(() => setLoading(false));
  }, [searchParams]);

  const filteredDocs = useMemo(() => {
    if (!searchTerm.trim()) return documents;
    const lower = searchTerm.toLowerCase();
    return documents.filter((d) => d.display_name.toLowerCase().includes(lower));
  }, [documents, searchTerm]);

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto p-6 w-full overflow-y-auto">
        <h1 className="text-xl font-semibold mb-1">Dokumen Akademik</h1>
        <p className="text-sm text-slate-500 mb-5">
          Kumpulan dokumen resmi: peraturan akademik, kurikulum, dan informasi wisuda.
        </p>

        <div className="relative mb-5 max-w-sm">
          <label htmlFor="doc-search" className="sr-only">Cari dokumen dalam koleksi</label>
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true" />
          <input
            id="doc-search"
            type="search"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Cari dokumen dalam koleksi ini..."
            className="w-full bg-white border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500/40"
          />
        </div>

        {loading ? (
          <p className="text-sm text-slate-400" role="status">Memuat dokumen...</p>
        ) : filteredDocs.length === 0 ? (
          <div className="border border-dashed border-slate-300 rounded-xl p-10 text-center bg-white text-sm text-slate-500">
            {documents.length === 0 ? "Belum ada dokumen resmi yang tersedia." : "Tidak ada dokumen yang cocok dengan pencarian."}
          </div>
        ) : (
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3 list-none" aria-label={`${filteredDocs.length} dokumen ditemukan`}>
            {filteredDocs.map((doc) => (
              <li key={doc.filename} className="bg-white border border-slate-200 rounded-xl p-4 flex items-start gap-3">
                <FileText size={22} className="text-red-500 shrink-0 mt-0.5" aria-hidden="true" />
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-slate-900 truncate">{doc.display_name}</div>
                  <div className="text-xs text-slate-400 mb-2">{doc.size_mb} MB</div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setViewingDoc({ source_file: doc.filename, page_number: 1, chunk_text: "", bbox: [] })}
                      className="text-xs text-blue-600 hover:underline"
                    >
                      Buka
                    </button>
                    <a
                      href={`${API_BASE}/documents/file/${encodeURIComponent(doc.filename)}`}
                      download
                      className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700"
                      aria-label={`Unduh ${doc.display_name}`}
                    >
                      <Download size={12} aria-hidden="true" /> Unduh
                    </a>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}

        {viewingDoc && <PdfViewer citation={viewingDoc} onClose={() => setViewingDoc(null)} />}
      </div>
    </AppShell>
  );
}

export default function DokumenPage() {
  return (
    <Suspense fallback={null}>
      <DokumenContent />
    </Suspense>
  );
}
