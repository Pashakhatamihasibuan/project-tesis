import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Riwayat Chat",
  description: "Lihat kembali percakapan sebelumnya dengan AI Assistant AkademiQ.",
  robots: { index: false, follow: false }, // data personal, tidak perlu terindeks mesin pencari
};

export default function RiwayatLayout({ children }: { children: React.ReactNode }) {
  return children;
}
