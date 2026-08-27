"use client";

import { useState, useMemo } from "react";
import { Search, HelpCircle } from "lucide-react";
import AppShell from "@/components/AppShell";

const FAQ_ITEMS = [
  {
    category: "Akun & Akses",
    question: "Bagaimana cara membuat akun di AkademiQ?",
    answer: "Klik tombol \"Daftar\" di halaman masuk, lalu lengkapi nama, email, username, dan kata sandi. Akun langsung aktif setelah pendaftaran.",
  },
  {
    category: "Akun & Akses",
    question: "Apa yang harus dilakukan jika lupa kata sandi?",
    answer: "Klik \"Lupa kata sandi?\" di halaman masuk, masukkan email terdaftar, lalu ikuti tautan reset yang dikirimkan.",
  },
  {
    category: "Chat",
    question: "Apakah saya harus login untuk menggunakan chat?",
    answer: "Tidak. Anda bisa mencoba chat sebagai tamu, tapi riwayat percakapan tamu tidak akan tersimpan. Login diperlukan hanya jika ingin menyimpan riwayat.",
  },
  {
    category: "Chat",
    question: "Apakah riwayat chat akan tersimpan?",
    answer: "Ya, jika Anda login. Semua percakapan tersimpan otomatis dan dapat dilihat kembali di halaman Riwayat Chat, termasuk dihapus satu per satu jika diinginkan.",
  },
  {
    category: "Dokumen",
    question: "Apa saja tipe file yang didukung untuk dokumen resmi?",
    answer: "Saat ini AkademiQ mendukung dokumen berformat PDF.",
  },
  {
    category: "Dokumen",
    question: "Apakah ada batasan ukuran file untuk upload?",
    answer: "Ya, ukuran maksimal file yang dapat diupload adalah 50 MB per file (khusus untuk admin pengelola dokumen resmi).",
  },
  {
    category: "Sistem & Fitur",
    question: "Bagaimana cara mencari materi atau dokumen?",
    answer: "Gunakan kolom pencarian di bagian atas halaman, atau jelajahi langsung daftar dokumen di halaman Dokumen.",
  },
  {
    category: "Sistem & Fitur",
    question: "Apa perbedaan Standard RAG, HyDE RAG, dan Re-ranking RAG?",
    answer: "Ketiganya adalah strategi pencarian dokumen yang berbeda sebelum AI menyusun jawaban. Anda dapat memilihnya di halaman Chat untuk membandingkan kualitas jawaban.",
  },
];

export default function FaqPage() {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredItems = useMemo(() => {
    if (!searchTerm.trim()) return FAQ_ITEMS;
    const lower = searchTerm.toLowerCase();
    return FAQ_ITEMS.filter(
      (item) => item.question.toLowerCase().includes(lower) || item.answer.toLowerCase().includes(lower)
    );
  }, [searchTerm]);

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto p-6 w-full overflow-y-auto">
        <h1 className="text-xl font-semibold mb-1">Bantuan FAQ</h1>
        <p className="text-sm text-slate-500 mb-5">Temukan jawaban atas pertanyaan yang sering diajukan.</p>

        <div className="relative mb-5">
          <label htmlFor="faq-search" className="sr-only">Cari pertanyaan</label>
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true" />
          <input
            id="faq-search"
            type="search"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Cari pertanyaan..."
            className="w-full bg-white border border-slate-200 rounded-lg pl-9 pr-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/40"
          />
        </div>

        {filteredItems.length === 0 ? (
          <div className="border border-dashed border-slate-300 rounded-xl p-8 text-center bg-white text-sm text-slate-500">
            Tidak ditemukan pertanyaan yang cocok dengan pencarian Anda.
          </div>
        ) : (
          <div className="space-y-2">
            {filteredItems.map((item, i) => (
              // <details>/<summary> native HTML: accordion accessible
              // bawaan browser (keyboard Enter/Space, screen reader
              // otomatis umumkan expanded/collapsed) tanpa perlu
              // state React atau ARIA manual sama sekali.
              <details key={i} className="bg-white border border-slate-200 rounded-xl group">
                <summary className="flex items-start gap-3 p-4 cursor-pointer list-none">
                  <HelpCircle size={18} className="text-blue-500 mt-0.5 shrink-0" aria-hidden="true" />
                  <span className="text-sm font-medium text-slate-900">{item.question}</span>
                </summary>
                <p className="text-sm text-slate-600 px-4 pb-4 pl-[calc(1.125rem+0.75rem+1.5rem)]">
                  {item.answer}
                </p>
              </details>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
