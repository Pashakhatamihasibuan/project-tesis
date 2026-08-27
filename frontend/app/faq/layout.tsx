import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Bantuan & FAQ",
  description: "Pertanyaan yang sering diajukan seputar penggunaan AkademiQ.",
};

export default function FaqLayout({ children }: { children: React.ReactNode }) {
  return children;
}
