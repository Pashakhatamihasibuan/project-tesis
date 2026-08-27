"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldAlert, Mail, Lock } from "lucide-react";
import { adminLogin } from "@/lib/api";

export default function AdminLoginPage() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await adminLogin(identifier, password);
      router.push("/upload");
    } catch (err: any) {
      setError(err.message || "Login gagal.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4">
      <div className="bg-white rounded-2xl w-full max-w-sm p-6">
        <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center text-white mb-4">
          <ShieldAlert size={20} />
        </div>
        <h1 className="text-lg font-semibold text-slate-900 mb-1">AkademiQ — Admin</h1>
        <p className="text-sm text-slate-500 mb-5">
          Halaman ini khusus pengelola dokumen resmi. Bukan untuk mahasiswa.
        </p>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="relative">
            <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              required
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="Email atau Username admin"
              className="w-full bg-slate-100 rounded-lg pl-9 pr-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-slate-500/40"
            />
          </div>
          <div className="relative">
            <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              required
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Kata Sandi"
              className="w-full bg-slate-100 rounded-lg pl-9 pr-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-slate-500/40"
            />
          </div>

          {error && <p className="text-xs text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-slate-800 hover:bg-slate-900 disabled:opacity-60 text-white text-sm font-medium rounded-lg py-2.5"
          >
            {loading ? "Memproses..." : "Masuk sebagai Admin"}
          </button>
        </form>
      </div>
    </div>
  );
}
