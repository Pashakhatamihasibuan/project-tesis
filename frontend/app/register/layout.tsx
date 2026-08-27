import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Daftar Akun",
  description: "Buat akun AkademiQ baru untuk mulai belajar lebih cerdas bersama AI Assistant.",
};

export default function RegisterLayout({ children }: { children: React.ReactNode }) {
  return children;
}
