"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home, MessageCircle, FileText, Clock, HelpCircle, Info,
  LogIn, LogOut, Bell, GraduationCap, FolderLock,
} from "lucide-react";
import { getToken, logout } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/", label: "Beranda", icon: Home },
  { href: "/chat", label: "Chat", icon: MessageCircle },
  { href: "/dokumen", label: "Dokumen", icon: FileText },
  { href: "/dokumen-pribadi", label: "Dokumen Pribadi", icon: FolderLock },
  { href: "/riwayat", label: "Riwayat Chat", icon: Clock },
  { href: "/faq", label: "Bantuan FAQ", icon: HelpCircle },
  { href: "/tentang", label: "Tentang Sistem", icon: Info },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isAuthed, setIsAuthed] = useState(false);

  useEffect(() => {
    setIsAuthed(!!getToken());
  }, [pathname]);

  function handleLogout() {
    logout();
    setIsAuthed(false);
    window.location.href = "/";
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Header -- role="banner" implisit lewat <header>, search decorative
          tapi tetap punya label untuk screen reader */}
      <header className="h-16 border-b border-slate-200 bg-white flex items-center gap-4 px-6 shrink-0">
        <Link href="/" className="flex items-center gap-2 font-semibold text-lg text-slate-900 w-48 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white" aria-hidden="true">
            <GraduationCap size={18} />
          </div>
          AkademiQ
        </Link>

        <form role="search" className="flex-1 max-w-xl" onSubmit={(e) => e.preventDefault()}>
          <label htmlFor="global-search" className="sr-only">
            Cari materi, topik, atau dokumen
          </label>
          <input
            id="global-search"
            type="search"
            placeholder="Cari materi, topik, atau dokumen..."
            className="w-full bg-slate-100 rounded-lg px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500/40"
          />
        </form>

        <div className="flex-1" />

        {isAuthed ? (
          <div className="flex items-center gap-3">
            <button aria-label="Notifikasi" className="relative text-slate-500 hover:text-slate-700">
              <Bell size={20} aria-hidden="true" />
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 text-sm text-slate-600 hover:text-red-600 border border-slate-200 rounded-lg px-3 py-1.5"
            >
              <LogOut size={14} aria-hidden="true" /> Keluar
            </button>
          </div>
        ) : (
          <Link
            href="/login"
            className="flex items-center gap-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg px-4 py-2"
          >
            <LogIn size={14} aria-hidden="true" /> Masuk
          </Link>
        )}
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* nav landmark eksplisit + aria-current="page" pada link aktif
            -- screen reader mengumumkan "Chat, halaman saat ini" */}
        <nav aria-label="Navigasi utama" className="w-56 border-r border-slate-200 bg-white shrink-0 overflow-y-auto">
          <ul className="p-3 space-y-1 list-none">
            {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
              const isActive = pathname === href;
              return (
                <li key={href}>
                  <Link
                    href={href}
                    aria-current={isActive ? "page" : undefined}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                      isActive ? "bg-blue-50 text-blue-700 font-medium" : "text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    <Icon size={17} aria-hidden="true" />
                    {label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <main id="main-content" className="flex-1 overflow-hidden flex flex-col">
          {children}
        </main>
      </div>
    </div>
  );
}
