import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dokumen Pribadi",
  description: "Kelola dokumen pribadi Anda untuk ditanya-jawabkan secara terpisah dari dokumen resmi.",
  robots: { index: false, follow: false },
};

export default function DokumenPribadiLayout({ children }: { children: React.ReactNode }) {
  return children;
}
