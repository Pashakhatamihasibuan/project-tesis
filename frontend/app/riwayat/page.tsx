"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Lock, MessageCircle, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import { fetchHistory, deleteHistoryEntry, getToken } from "@/lib/api";
import AppShell from "@/components/AppShell";

type HistoryEntry = {
  id: number;
  question: string;
  answer: string;
  configuration: string;
  created_at: string;
};

const PAGE_SIZE = 10;

export default function RiwayatPage() {
  const [isAuthed, setIsAuthed] = useState(false);
  const [items, setItems] = useState<HistoryEntry[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const loadPage = useCallback(async (pageNum: number) => {
    setLoading(true);
    const data = await fetchHistory(pageNum, PAGE_SIZE);
    if (data) {
      setItems(data.items);
      setTotalPages(data.total_pages);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    const authed = !!getToken();
    setIsAuthed(authed);
    if (authed) loadPage(1);
    else setLoading(false);
  }, [loadPage]);

  async function handleDelete(id: number) {
    setDeletingId(id);
    try {
      await deleteHistoryEntry(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
    } finally {
      setDeletingId(null);
    }
  }

  function goToPage(newPage: number) {
    setPage(newPage);
    loadPage(newPage);
  }

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto p-6 w-full overflow-y-auto">
        <h1 className="text-xl font-semibold mb-1">Riwayat Chat</h1>
        <p className="text-sm text-slate-500 mb-5">
          {isAuthed ? "Percakapan Anda tersimpan otomatis." : "Masuk untuk melihat dan menyimpan riwayat percakapan."}
        </p>

        {loading ? (
          <p className="text-sm text-slate-400" role="status">Memuat...</p>
        ) : !isAuthed ? (
          <div className="border border-dashed border-slate-300 rounded-xl p-10 text-center bg-white">
            <Lock size={28} className="mx-auto text-slate-300 mb-3" aria-hidden="true" />
            <p className="text-sm text-slate-500 mb-4">Riwayat chat hanya tersedia untuk pengguna yang masuk.</p>
            <Link href="/login" className="inline-block bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg px-4 py-2">
              Masuk Sekarang
            </Link>
          </div>
        ) : items.length === 0 ? (
          <div className="border border-dashed border-slate-300 rounded-xl p-10 text-center bg-white text-sm text-slate-500">
            Belum ada percakapan. Mulai chat baru untuk melihatnya di sini.
          </div>
        ) : (
          <>
            <ul className="space-y-3 list-none">
              {items.map((h) => (
                <li key={h.id} className="bg-white border border-slate-200 rounded-xl p-4">
                  <div className="flex gap-3">
                    <MessageCircle size={18} className="text-blue-500 mt-0.5 shrink-0" aria-hidden="true" />
                    <div className="min-w-0 flex-1">
                      <div className="font-medium text-sm text-slate-900">{h.question}</div>
                      <div className="text-xs text-slate-500 mt-1 line-clamp-2">{h.answer}</div>
                      <div className="text-[11px] text-slate-400 mt-2 flex gap-3">
                        <span>{new Date(h.created_at).toLocaleString("id-ID")}</span>
                        <span className="bg-slate-100 rounded px-1.5">{h.configuration}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(h.id)}
                      disabled={deletingId === h.id}
                      aria-label={`Hapus percakapan: ${h.question}`}
                      className="text-slate-400 hover:text-red-600 disabled:opacity-40 shrink-0"
                    >
                      <Trash2 size={16} aria-hidden="true" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>

            {totalPages > 1 && (
              <nav aria-label="Navigasi halaman riwayat" className="flex items-center justify-center gap-3 mt-5">
                <button
                  onClick={() => goToPage(page - 1)}
                  disabled={page <= 1}
                  aria-label="Halaman sebelumnya"
                  className="p-1.5 rounded hover:bg-slate-200 disabled:opacity-30"
                >
                  <ChevronLeft size={16} aria-hidden="true" />
                </button>
                <span className="text-xs text-slate-600" aria-current="page">
                  Halaman {page} dari {totalPages}
                </span>
                <button
                  onClick={() => goToPage(page + 1)}
                  disabled={page >= totalPages}
                  aria-label="Halaman berikutnya"
                  className="p-1.5 rounded hover:bg-slate-200 disabled:opacity-30"
                >
                  <ChevronRight size={16} aria-hidden="true" />
                </button>
              </nav>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}
