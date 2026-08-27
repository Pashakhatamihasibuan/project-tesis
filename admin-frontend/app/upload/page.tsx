"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut, UploadCloud, RefreshCw } from "lucide-react";
import { getAdminToken, clearAdminToken, uploadDocument, rebuildIndex } from "@/lib/api";

export default function AdminUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("");
  const [checking, setChecking] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Guard sisi UI: kalau tidak ada token tersimpan, tendang ke login.
    // Ini kenyamanan UX saja -- pertahanan sesungguhnya tetap di backend
    // (require_admin) yang akan menolak 403 walau token dipalsukan.
    if (!getAdminToken()) {
      router.replace("/login");
    } else {
      setChecking(false);
    }
  }, [router]);

  function handleLogout() {
    clearAdminToken();
    router.push("/login");
  }

  async function handleUpload() {
    if (!file) return;
    setStatus("Mengupload...");
    try {
      const data = await uploadDocument(file);
      setStatus(`Berhasil diupload: ${data.filename}`);
    } catch (err: any) {
      if (err.message?.includes("ditolak")) {
        handleLogout(); // token invalid/expired -> paksa login ulang
      }
      setStatus(err.message || "Upload gagal.");
    }
  }

  async function handleRebuild() {
    setStatus("Membangun ulang index (3 model embedding)...");
    try {
      const data = await rebuildIndex(false);
      setStatus(`Index dibangun ulang: ${data.total_chunks} chunk dari ${data.total_documents} dokumen.`);
    } catch (err: any) {
      if (err.message?.includes("ditolak")) {
        handleLogout();
      }
      setStatus(err.message || "Rebuild gagal.");
    }
  }

  if (checking) return null;

  return (
    <div className="max-w-lg mx-auto p-8 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Upload Dokumen Resmi</h1>
        <button onClick={handleLogout} className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-red-600">
          <LogOut size={13} /> Keluar
        </button>
      </div>
      <p className="text-sm text-slate-500">
        Halaman ini tidak ditautkan dari navigasi aplikasi mahasiswa. Endpoint backend
        dilindungi RBAC — sesi non-admin otomatis ditolak.
      </p>

      <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center">
        <UploadCloud size={28} className="mx-auto text-slate-400 mb-2" />
        <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} className="text-sm" />
      </div>

      <div className="flex gap-2">
        <button onClick={handleUpload} disabled={!file} className="bg-blue-600 disabled:opacity-40 text-white rounded px-4 py-2 text-sm">
          Upload Dokumen
        </button>
        <button onClick={handleRebuild} className="flex items-center gap-1.5 bg-slate-700 text-white rounded px-4 py-2 text-sm">
          <RefreshCw size={14} /> Rebuild Index (3 model)
        </button>
      </div>

      {status && <p className="text-sm text-slate-700 bg-slate-100 rounded-lg px-3 py-2">{status}</p>}
    </div>
  );
}
