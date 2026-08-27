"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { GraduationCap, ArrowLeft } from "lucide-react";
import { forgotPassword } from "@/lib/api";
import { forgotPasswordSchema, type ForgotPasswordFormValues } from "@/lib/validation";

export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordFormValues>({ resolver: zodResolver(forgotPasswordSchema) });

  async function onSubmit(values: ForgotPasswordFormValues) {
    await forgotPassword(values.email);
    // Selalu tampilkan sukses, terlepas email terdaftar atau tidak --
    // konsisten dengan desain keamanan backend (cegah user enumeration).
    setSubmitted(true);
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-sm p-6 shadow-sm border border-slate-100">
        <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white mb-4" aria-hidden="true">
          <GraduationCap size={20} />
        </div>

        {submitted ? (
          <div role="status">
            <h1 className="text-lg font-semibold text-slate-900 mb-1">Periksa email Anda</h1>
            <p className="text-sm text-slate-500 mb-5">
              Jika email tersebut terdaftar, kami telah mengirimkan tautan untuk mereset kata sandi.
              Tautan berlaku selama 30 menit.
            </p>
          </div>
        ) : (
          <>
            <h1 className="text-lg font-semibold text-slate-900 mb-1">Lupa Kata Sandi?</h1>
            <p className="text-sm text-slate-500 mb-5">
              Masukkan email akun Anda, kami akan kirimkan tautan reset kata sandi.
            </p>

            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-3">
              <div>
                <label htmlFor="email" className="sr-only">Email</label>
                <input
                  id="email"
                  type="email"
                  {...register("email")}
                  placeholder="Email terdaftar"
                  aria-invalid={!!errors.email}
                  aria-describedby={errors.email ? "email-error" : undefined}
                  className="w-full bg-slate-100 rounded-lg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/40"
                />
                {errors.email && (
                  <p id="email-error" role="alert" className="text-xs text-red-600 mt-1">
                    {errors.email.message}
                  </p>
                )}
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm font-medium rounded-lg py-2.5"
              >
                {isSubmitting ? "Mengirim..." : "Kirim Tautan Reset"}
              </button>
            </form>
          </>
        )}

        <Link href="/login" className="flex items-center gap-1.5 justify-center text-xs text-slate-500 hover:text-blue-600 mt-5">
          <ArrowLeft size={13} aria-hidden="true" /> Kembali ke halaman masuk
        </Link>
      </div>
    </div>
  );
}
