import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Masuk",
  description: "Masuk ke akun AkademiQ untuk menyimpan riwayat percakapan Anda.",
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return children;
}
