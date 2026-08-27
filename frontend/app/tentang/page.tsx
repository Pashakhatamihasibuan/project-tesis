import { Eye, GraduationCap, BookOpen, Target, MessageCircle, FileText, Clock, Bookmark, Shield } from "lucide-react";
import AppShell from "@/components/AppShell";

const MISI_ITEMS = [
  { icon: GraduationCap, text: "Menyediakan bantuan belajar berbasis AI yang akurat dan mudah dipahami." },
  { icon: BookOpen, text: "Memudahkan akses informasi akademik dan referensi terpercaya." },
  { icon: Target, text: "Meningkatkan efektivitas dan efisiensi proses belajar mahasiswa." },
];

const FITUR_UTAMA = [
  { icon: MessageCircle, text: "AI Chat Assistant" },
  { icon: FileText, text: "Pencarian Dokumen Akademik" },
  { icon: Clock, text: "Riwayat Percakapan" },
  { icon: Bookmark, text: "Topik Populer" },
  { icon: Shield, text: "Keamanan Data Terjamin" },
];

export default function TentangSistemPage() {
  return (
    <AppShell>
      <div className="max-w-3xl mx-auto p-6 w-full overflow-y-auto">
        <h1 className="text-xl font-semibold mb-5">Tentang Sistem</h1>

        <article className="bg-white border border-slate-200 rounded-2xl p-6 mb-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white" aria-hidden="true">
              <GraduationCap size={20} />
            </div>
            <h2 className="text-lg font-semibold text-slate-900">AkademiQ</h2>
          </div>
          <p className="text-sm text-slate-600 leading-relaxed">
            AkademiQ adalah platform AI Assistant yang dirancang khusus untuk membantu mahasiswa
            Program Studi S2 Pendidikan Teknik Elektronika dan Informatika UNY dalam memahami materi
            akademik, mencari referensi, dan belajar lebih efektif dengan dukungan teknologi kecerdasan
            buatan berbasis Retrieval Augmented Generation (RAG).
          </p>
        </article>

        <section aria-labelledby="visi-heading" className="bg-white border border-slate-200 rounded-2xl p-6 mb-5">
          <h2 id="visi-heading" className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-2">
            <Eye size={16} className="text-blue-500" aria-hidden="true" /> Visi
          </h2>
          <p className="text-sm text-slate-600">
            Menjadi platform AI akademik terdepan yang membantu setiap mahasiswa mencapai potensi
            belajar terbaiknya dengan mudah, cepat, dan cerdas.
          </p>
        </section>

        <section aria-labelledby="misi-heading" className="mb-5">
          <h2 id="misi-heading" className="text-sm font-semibold text-slate-900 mb-3">Misi</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {MISI_ITEMS.map((item, i) => (
              <div key={i} className="bg-white border border-slate-200 rounded-xl p-4 text-center">
                <item.icon size={22} className="mx-auto text-blue-500 mb-2" aria-hidden="true" />
                <p className="text-xs text-slate-600">{item.text}</p>
              </div>
            ))}
          </div>
        </section>

        <section aria-labelledby="fitur-heading" className="bg-white border border-slate-200 rounded-2xl p-6">
          <h2 id="fitur-heading" className="text-sm font-semibold text-slate-900 mb-3">Fitur Utama</h2>
          <ul className="space-y-2 list-none">
            {FITUR_UTAMA.map((item, i) => (
              <li key={i} className="flex items-center gap-3 text-sm text-slate-600 py-1.5 border-b border-slate-50 last:border-0">
                <item.icon size={16} className="text-slate-400" aria-hidden="true" />
                {item.text}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </AppShell>
  );
}
