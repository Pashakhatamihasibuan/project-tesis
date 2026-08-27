import "./globals.css";

export const metadata = {
  title: "AkademiQ Admin",
  description: "Panel admin AkademiQ — upload & kelola dokumen resmi",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id">
      <body className="bg-slate-50 text-slate-800">{children}</body>
    </html>
  );
}
