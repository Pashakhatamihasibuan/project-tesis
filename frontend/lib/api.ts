const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  // Catatan: artifacts Claude tidak boleh pakai localStorage, tapi ini
  // adalah kode UNTUK PROJECT NYATA kamu (dijalankan di browser biasa
  // luar sandbox Claude), jadi localStorage aman & normal dipakai di sini.
  return window.localStorage.getItem("akademiq_token");
}

export function setToken(token: string) {
  window.localStorage.setItem("akademiq_token", token);
}

export function clearToken() {
  window.localStorage.removeItem("akademiq_token");
}

export function logout() {
  clearToken();
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function login(identifier: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identifier, password }),
  });
  if (!res.ok) throw new Error("Login gagal");
  const data = await res.json();
  setToken(data.access_token);
  return data;
}

export async function register(payload: {
  email: string;
  username: string;
  password: string;
  full_name: string;
  institution?: string;
}) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Registrasi gagal");
  const data = await res.json();
  setToken(data.access_token);
  return data;
}

export async function fetchHistory(page: number = 1, pageSize: number = 20) {
  const res = await fetch(`${API_BASE}/history?page=${page}&page_size=${pageSize}`, { headers: authHeaders() });
  if (!res.ok) return null; // guest atau token invalid
  return res.json();
}

export async function deleteHistoryEntry(entryId: number) {
  const res = await fetch(`${API_BASE}/history/${entryId}`, { method: "DELETE", headers: authHeaders() });
  if (!res.ok) throw new Error("Gagal menghapus riwayat.");
  return res.json();
}

export async function forgotPassword(email: string) {
  const res = await fetch(`${API_BASE}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  return res.json(); // selalu sukses generik (lihat catatan keamanan di backend)
}

export async function resetPassword(token: string, newPassword: string) {
  const res = await fetch(`${API_BASE}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Reset password gagal.");
  }
  return res.json();
}

export async function fetchPublicDocuments() {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) return { documents: [], total: 0 };
  return res.json();
}

/**
 * Streaming chat via SSE. onToken dipanggil tiap token baru,
 * onCitations dipanggil sekali di akhir dengan daftar sumber dokumen.
 */
export async function streamChat(
  query: string,
  architecture: string,
  embedding: string,
  onToken: (token: string) => void,
  onCitations: (citations: any[]) => void
) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ query, architecture, embedding }),
  });

  if (!res.body) throw new Error("Streaming tidak didukung oleh browser ini");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const event = JSON.parse(line.slice(6));
      if (event.type === "token") onToken(event.content);
      if (event.type === "citations") onCitations(event.content);
    }
  }
}
