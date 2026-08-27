"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { GraduationCap, Mail, Lock } from "lucide-react";
import { login } from "@/lib/api";
import { loginSchema, type LoginFormValues } from "@/lib/validation";

export default function LoginPage() {
  const [serverError, setServerError] = useState("");
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });

  async function onSubmit(values: LoginFormValues) {
    setServerError("");
    try {
      await login(values.identifier, values.password);
      router.push("/chat");
    } catch {
      setServerError("Email/username atau kata sandi salah.");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-sm p-6 shadow-sm border border-slate-100">
        <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white mb-4" aria-hidden="true">
          <GraduationCap size={20} />
        </div>
        <h1 className="text-lg font-semibold text-slate-900 mb-1">Selamat datang kembali!</h1>
        <p className="text-sm text-slate-500 mb-5">Masuk untuk menyimpan riwayat chat Anda.</p>

        {/* noValidate: kita pakai validasi Zod sendiri, bukan validasi
            HTML5 browser default (supaya pesan error konsisten & dalam
            Bahasa Indonesia) */}
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-3">
          <div>
            <label htmlFor="identifier" className="sr-only">Email atau Username</label>
            <div className="relative">
              <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true" />
              <input
                id="identifier"
                {...register("identifier")}
                placeholder="Email atau Username"
                aria-invalid={!!errors.identifier}
                aria-describedby={errors.identifier ? "identifier-error" : undefined}
                className="w-full bg-slate-100 rounded-lg pl-9 pr-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/40"
              />
            </div>
            {errors.identifier && (
              <p id="identifier-error" role="alert" className="text-xs text-red-600 mt-1">
                {errors.identifier.message}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="sr-only">Kata Sandi</label>
            <div className="relative">
              <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true" />
              <input
                id="password"
                type="password"
                {...register("password")}
                placeholder="Kata Sandi"
                aria-invalid={!!errors.password}
                aria-describedby={errors.password ? "password-error" : undefined}
                className="w-full bg-slate-100 rounded-lg pl-9 pr-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/40"
              />
            </div>
            {errors.password && (
              <p id="password-error" role="alert" className="text-xs text-red-600 mt-1">
                {errors.password.message}
              </p>
            )}
          </div>

          <div className="text-right">
            <Link href="/forgot-password" className="text-xs text-blue-600 hover:underline">
              Lupa kata sandi?
            </Link>
          </div>

          {serverError && (
            <p role="alert" className="text-xs text-red-600">{serverError}</p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm font-medium rounded-lg py-2.5"
          >
            {isSubmitting ? "Memproses..." : "Masuk"}
          </button>
        </form>

        <p className="text-xs text-slate-400 text-center mt-4">
          Belum punya akun?{" "}
          <Link href="/register" className="text-blue-600 font-medium">Daftar sekarang</Link>
        </p>
        <p className="text-xs text-slate-400 text-center mt-2">
          <Link href="/chat" className="underline">Lanjutkan sebagai tamu</Link>
        </p>
      </div>
    </div>
  );
}
