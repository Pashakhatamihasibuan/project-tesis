import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Chat",
  description: "Tanya jawab akademik dengan AI Assistant AkademiQ berbasis dokumen resmi UNY.",
};

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return children;
}
