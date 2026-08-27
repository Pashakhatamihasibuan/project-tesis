import type { Metadata, Viewport } from "next";
import "./globals.css";

// SEO: metadata dasar diwariskan semua halaman, tiap halaman child bisa
// override title/description sendiri lewat export const metadata lokal
// (lihat app/faq/page.tsx dkk). openGraph disiapkan untuk preview link
// yang lebih baik saat dibagikan (WhatsApp/Telegram grup mahasiswa).
export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: {
    default: "AkademiQ — Asisten Akademik S2 PTEI UNY",
    template: "%s | AkademiQ",
  },
  description:
    "Chatbot akademik berbasis AI untuk mahasiswa Program Studi S2 Pendidikan Teknik Elektronika dan Informatika UNY. Tanya jawab peraturan akademik, kurikulum, dan prosedur administratif berbasis dokumen resmi.",
  keywords: ["AkademiQ", "chatbot akademik", "UNY", "S2 PTEI", "RAG", "asisten AI mahasiswa"],
  robots: { index: true, follow: true },
  openGraph: {
    type: "website",
    locale: "id_ID",
    siteName: "AkademiQ",
    title: "AkademiQ — Asisten Akademik S2 PTEI UNY",
    description: "Chatbot akademik berbasis AI untuk mahasiswa S2 PTEI UNY.",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#2563eb",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id">
      <body className="bg-slate-50 text-slate-800">
        {/* Skip-to-content link -- accessibility (WCAG 2.4.1 Bypass
            Blocks). Tersembunyi secara visual sampai pengguna keyboard
            menekan Tab, supaya mereka tidak perlu Tab lewat seluruh
            sidebar navigasi tiap pindah halaman. */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:bg-blue-600 focus:text-white focus:px-4 focus:py-2 focus:rounded-lg"
        >
          Langsung ke konten utama
        </a>
        {children}
      </body>
    </html>
  );
}
