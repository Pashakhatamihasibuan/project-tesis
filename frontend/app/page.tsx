"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { MessageCircle, FileText, GraduationCap } from "lucide-react";
import { fetchPublicDocuments } from "@/lib/api";
import AppShell from "@/components/AppShell";

type DocumentItem = { filename: string; display_name: string; size_mb: number };

export default function BerandaPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPublicDocuments()
      .then((data) => setDocuments(data.documents.slice(0, 5)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto p-6 w-full overflow-y-auto">
        <section
          aria-labelledby="welcome-heading"
          className="bg-gradient-to-br from-blue-50 to-white border border-blue-100 rounded-2xl p-8 mb-6 flex items-center gap-6"
        >
          <div className="flex-1">
            <h1 id="welcome-heading" className="text-2xl font-semibold text-slate-900 mb-2">
              Selamat datang kembali!
            </h1>
            <p className="text-sm text-slate-600 mb-4 max-w-md">
              Temukan materi, dokumen resmi, dan tanya jawab akademik dengan mudah bersama AkademiQ.
            </p>
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg px-5 py-2.5"
            >
              <MessageCircle size={16} aria-hidden="true" /> Mulai Chat
            </Link>
          </div>
          <GraduationCap size={80} className="text-blue-200 shrink-0" aria-hidden="true" />
        </section>

        <section aria-labelledby="recent-docs-heading">
          <div className="flex items-center justify-between mb-3">
            <h2 id="recent-docs-heading" className="text-lg font-semibold text-slate-900">
              Dokumen Terbaru
            </h2>
            <Link href="/dokumen" className="text-xs text-blue-600 hover:underline">
              Lihat semua dokumen
            </Link>
          </div>

          {loading ? (
            <p className="text-sm text-slate-400" role="status">Memuat dokumen...</p>
          ) : documents.length === 0 ? (
            <div className="border border-dashed border-slate-300 rounded-xl p-8 text-center bg-white text-sm text-slate-500">
              Belum ada dokumen resmi yang tersedia.
            </div>
          ) : (
            <ul className="space-y-2 list-none">
              {documents.map((doc) => (
                <li key={doc.filename}>
                  <Link
                    href={`/dokumen?file=${encodeURIComponent(doc.filename)}`}
                    className="flex items-center gap-3 bg-white border border-slate-200 rounded-xl p-4 hover:border-blue-300 transition-colors"
                  >
                    <FileText size={20} className="text-red-500 shrink-0" aria-hidden="true" />
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium text-slate-900 truncate">{doc.display_name}</div>
                      <div className="text-xs text-slate-400">{doc.size_mb} MB</div>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </AppShell>
  );
}
