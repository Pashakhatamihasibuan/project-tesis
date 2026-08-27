import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dokumen Akademik",
  description: "Jelajahi dokumen resmi akademik S2 PTEI UNY: peraturan, kurikulum, dan informasi wisuda.",
};

export default function DokumenLayout({ children }: { children: React.ReactNode }) {
  return children;
}
