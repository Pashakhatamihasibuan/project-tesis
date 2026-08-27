"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FolderLock, Lock, Construction } from "lucide-react";
import { getToken } from "@/lib/api";
import AppShell from "@/components/AppShell";

export default function DokumenPribadiPage() {
  const [isAuthed, setIsAuthed] = useState(false);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    setIsAuthed(!!getToken());
    setChecked(true);
  }, []);

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto p-6 w-full overflow-y-auto">
        <h1 className="text-xl font-semibold mb-1">Dokumen Pribadi</h1>
        <p className="text-sm text-slate-500 mb-5">
          Unggah dokumen milik Anda sendiri untuk ditanya-jawabkan, terpisah dari dokumen resmi UNY.
        </p>

        {!checked ? null : !isAuthed ? (
          <div className="border border-dashed border-slate-300 rounded-xl p-10 text-center bg-white">
            <Lock size={28} className="mx-auto text-slate-300 mb-3" aria-hidden="true" />
            <p className="text-sm text-slate-500 mb-4">Fitur ini hanya tersedia untuk pengguna yang masuk.</p>
            <Link href="/login" className="inline-block bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg px-4 py-2">
              Masuk Sekarang
            </Link>
          </div>
        ) : (
          <div role="status" className="border border-dashed border-amber-300 bg-amber-50 rounded-xl p-10 text-center">
            <Construction size={28} className="mx-auto text-amber-400 mb-3" aria-hidden="true" />
            <h2 className="text-sm font-semibold text-amber-800 mb-1">Fitur dalam pengembangan</h2>
            <p className="text-sm text-amber-700 max-w-sm mx-auto">
              Kemampuan mengunggah dan menanyakan dokumen pribadi (terpisah dari indeks dokumen resmi)
              sedang dalam tahap pengembangan lanjutan dan belum tersedia di versi ini.
            </p>
          </div>
        )}

        <div className="flex items-start gap-2 text-xs text-slate-400 mt-4">
          <FolderLock size={14} className="mt-0.5 shrink-0" aria-hidden="true" />
          Dokumen pribadi nantinya akan disimpan terisolasi per akun dan diberi label
          &quot;bukan sumber resmi&quot;, tidak akan tercampur dengan jawaban berbasis dokumen UNY.
        </div>
      </div>
    </AppShell>
  );
}
