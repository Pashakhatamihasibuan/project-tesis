import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Tentang Sistem",
  description: "Informasi tentang AkademiQ: visi, misi, fitur utama, dan teknologi yang digunakan.",
};

export default function TentangLayout({ children }: { children: React.ReactNode }) {
  return children;
}
