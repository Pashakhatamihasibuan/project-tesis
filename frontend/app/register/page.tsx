"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { GraduationCap } from "lucide-react";
import { register as registerUser } from "@/lib/api";
import { registerSchema, type RegisterFormValues } from "@/lib/validation";

export default function RegisterPage() {
  const [serverError, setServerError] = useState("");
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({ resolver: zodResolver(registerSchema) });

  async function onSubmit(values: RegisterFormValues) {
    setServerError("");
    try {
      await registerUser({
        email: values.email,
        username: values.username,
        password: values.password,
        full_name: values.full_name,
        institution: values.institution || undefined,
      });
      router.push("/chat");
    } catch {
      setServerError("Registrasi gagal. Email atau username mungkin sudah dipakai.");
    }
  }

  // Helper kecil supaya tidak menulis pola label+input+error berulang
  // 6 kali -- tetap pakai <label htmlFor> asli (bukan div biasa) supaya
  // asosiasi label-input tetap valid untuk screen reader.
  function FieldError({ id, message }: { id: string; message?: string }) {
    if (!message) return null;
    return (
      <p id={id} role="alert" className="text-xs text-red-600 mt-1">
        {message}
      </p>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-sm p-6 shadow-sm border border-slate-100">
        <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white mb-4" aria-hidden="true">
          <GraduationCap size={20} />
        </div>
        <h1 className="text-lg font-semibold text-slate-900 mb-1">Buat Akun Baru</h1>
        <p className="text-sm text-slate-500 mb-5">Lengkapi data diri Anda untuk membuat akun AkademiQ.</p>

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-3">
          <div>
            <label htmlFor="full_name" className="sr-only">Nama Lengkap</label>
            <input
              id="full_name"
              {...register("full_name")}
              placeholder="Nama Lengkap"
              aria-invalid={!!errors.full_name}
              aria-describedby={errors.full_name ? "full_name-error" : undefined}
              className="w-full bg-slate-100 rounded-lg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/40"
            />
            <FieldError id="full_name-error" message={errors.full_name?.message} />
          </div>

          <div>
            <label htmlFor="email" className="sr-only">Email</label>
            <input
              id="email"
              type="email"
              {...register("email")}
              placeholder="Email"
              aria-invalid={!!errors.email}
              aria-describedby={errors.email ? "email-error" : undefined}
              className="w-full bg-slate-100 rounded-lg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/40"
            />
            <FieldError id="email-error" message={errors.email?.message} />
          </div>

          <div>
            <label htmlFor="username" className="sr-only">Username</label>
            <input
              id="username"
              {...register("username")}
              placeholder="Username"
              aria-invalid={!!errors.username}
              aria-describedby={errors.username ? "username-error" : undefined}
              className="w-full bg-slate-100 rounded-lg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/40"
            />
            <FieldError id="username-error" message={errors.username?.message} />
          </div>

          <div>
            <label htmlFor="password" className="sr-only">Buat kata sandi</label>
            <input
              id="password"
              type="password"
              {...register("password")}
              placeholder="Buat kata sandi"
              aria-invalid={!!errors.password}
              aria-describedby={errors.password ? "password-error" : "password-hint"}
              className="w-full bg-slate-100 rounded-lg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/40"
            />
            <p id="password-hint" className="text-[11px] text-slate-400 mt-1">
              Minimal 8 karakter, mengandung huruf dan angka.
            </p>
            <FieldError id="password-error" message={errors.password?.message} />
          </div>

          <div>
            <label htmlFor="confirmPassword" className="sr-only">Konfirmasi kata sandi</label>
            <input
              id="confirmPassword"
              type="password"
              {...register("confirmPassword")}
              placeholder="Konfirmasi kata sandi"
              aria-invalid={!!errors.confirmPassword}
              aria-describedby={errors.confirmPassword ? "confirmPassword-error" : undefined}
              className="w-full bg-slate-100 rounded-lg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/40"
            />
            <FieldError id="confirmPassword-error" message={errors.confirmPassword?.message} />
          </div>

          <div>
            <label htmlFor="institution" className="sr-only">Institusi (opsional)</label>
            <input
              id="institution"
              {...register("institution")}
              placeholder="Institusi (opsional)"
              className="w-full bg-slate-100 rounded-lg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/40"
            />
          </div>

          {serverError && <p role="alert" className="text-xs text-red-600">{serverError}</p>}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm font-medium rounded-lg py-2.5"
          >
            {isSubmitting ? "Memproses..." : "Daftar"}
          </button>
        </form>

        <p className="text-xs text-slate-400 text-center mt-4">
          Sudah punya akun?{" "}
          <Link href="/login" className="text-blue-600 font-medium">Masuk sekarang</Link>
        </p>
      </div>
    </div>
  );
}
