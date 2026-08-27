const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
const TOKEN_KEY = "akademiq_admin_token";

export function getAdminToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setAdminToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearAdminToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

function authHeaders(): Record<string, string> {
  const token = getAdminToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Login memanggil endpoint /auth/login yang SAMA dengan mahasiswa --
 * tidak ada endpoint login terpisah untuk admin di backend. Yang
 * membedakan adalah field `role` di response: kalau bukan "admin",
 * kita tolak di sisi UI (backend tetap jadi garis pertahanan
 * sesungguhnya lewat require_admin() di tiap endpoint /admin/*).
 */
export async function adminLogin(identifier: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identifier, password }),
  });
  if (!res.ok) throw new Error("Login gagal.");

  const data = await res.json();
  if (data.role !== "admin") {
    throw new Error("Akun ini bukan admin. Hubungi administrator sistem untuk promosi role.");
  }

  setAdminToken(data.access_token);
  return data;
}

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/admin/upload`, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });
  if (res.status === 403) throw new Error("Akses ditolak: sesi bukan admin.");
  if (!res.ok) throw new Error("Upload gagal.");
  return res.json();
}

export async function rebuildIndex(useDummyEmbedder: boolean = false) {
  const res = await fetch(`${API_BASE}/admin/rebuild-index?use_dummy_embedder=${useDummyEmbedder}`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (res.status === 403) throw new Error("Akses ditolak: sesi bukan admin.");
  if (!res.ok) throw new Error("Rebuild index gagal.");
  return res.json();
}
