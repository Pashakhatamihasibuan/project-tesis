"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { GraduationCap, CheckCircle2 } from "lucide-react";
import { resetPassword } from "@/lib/api";
import { resetPasswordSchema, type ResetPasswordFormValues } from "@/lib/validation";

function ResetPasswordForm() {
  const [serverError, setServerError] = useState("");
  const [success, setSuccess] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormValues>({ resolver: zodResolver(resetPasswordSchema) });

  async function onSubmit(values: ResetPasswordFormValues) {
    if (!token) {
      setServerError("Tautan reset tidak valid -- token tidak ditemukan di URL.");
      return;
    }
    setServerError("");
    try {
      await resetPassword(token, values.newPassword);
      setSuccess(true);
      setTimeout(() => router.push("/login"), 2000);
    } catch (err: any) {
      setServerError(err.message || "Reset password gagal.");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-sm p-6 shadow-sm border border-slate-100">
        <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white mb-4" aria-hidden="true">
          <GraduationCap size={20} />
        </div>

        {!token ? (
          <div role="alert">
            <h1 className="text-lg font-semibold text-slate-900 mb-1">Tautan tidak valid</h1>
            <p className="text-sm text-slate-500 mb-4">
              Tautan reset password ini tidak lengkap. Silakan minta tautan baru.
            </p>
            <Link href="/forgot-password" className="text-sm text-blue-600 font-medium">
              Minta tautan reset baru
            </Link>
          </div>
        ) : success ? (
          <div role="status" className="text-center py-4">
            <CheckCircle2 size={40} className="mx-auto text-emerald-500 mb-3" aria-hidden="true" />
            <h1 className="text-lg font-semibold text-slate-900 mb-1">Kata sandi berhasil direset</h1>
            <p className="text-sm text-slate-500">Mengalihkan ke halaman masuk...</p>
          </div>
        ) : (
          <>
            <h1 className="text-lg font-semibold text-slate-900 mb-1">Atur Kata Sandi Baru</h1>
            <p className="text-sm text-slate-500 mb-5">Masukkan kata sandi baru untuk akun Anda.</p>

            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-3">
              <div>
                <label htmlFor="newPassword" className="sr-only">Kata sandi baru</label>
                <input
                  id="newPassword"
                  type="password"
                  {...register("newPassword")}
                  placeholder="Kata sandi baru"
                  aria-invalid={!!errors.newPassword}
                  aria-describedby={errors.newPassword ? "newPassword-error" : undefined}
                  className="w-full bg-slate-100 rounded-lg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/40"
                />
                {errors.newPassword && (
                  <p id="newPassword-error" role="alert" className="text-xs text-red-600 mt-1">
                    {errors.newPassword.message}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="confirmPassword" className="sr-only">Konfirmasi kata sandi baru</label>
                <input
                  id="confirmPassword"
                  type="password"
                  {...register("confirmPassword")}
                  placeholder="Konfirmasi kata sandi baru"
                  aria-invalid={!!errors.confirmPassword}
                  aria-describedby={errors.confirmPassword ? "confirmPassword-error" : undefined}
                  className="w-full bg-slate-100 rounded-lg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/40"
                />
                {errors.confirmPassword && (
                  <p id="confirmPassword-error" role="alert" className="text-xs text-red-600 mt-1">
                    {errors.confirmPassword.message}
                  </p>
                )}
              </div>

              {serverError && <p role="alert" className="text-xs text-red-600">{serverError}</p>}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm font-medium rounded-lg py-2.5"
              >
                {isSubmitting ? "Memproses..." : "Reset Kata Sandi"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  // Suspense WAJIB di sini -- useSearchParams() butuh boundary ini
  // supaya Next.js bisa melakukan static prerendering pada build,
  // fallback ditampilkan sekejap saat search params masih di-resolve
  // di sisi client.
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-sm text-slate-400">Memuat...</div>}>
      <ResetPasswordForm />
    </Suspense>
  );
}
