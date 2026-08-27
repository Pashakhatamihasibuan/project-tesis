"use client";

import { useState, useRef, useEffect } from "react";
import { Send, AlertCircle, Paperclip } from "lucide-react";
import { streamChat, getToken } from "@/lib/api";
import PdfViewer, { Citation } from "@/components/PdfViewer";
import AppShell from "@/components/AppShell";

type Message = { role: "user" | "bot"; text: string; citations?: Citation[] };

const GREETING = "Halo! Saya AI Assistant AkademiQ. Ada yang bisa saya bantu terkait dokumen akademik UNY?";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([{ role: "bot", text: GREETING }]);
  const [input, setInput] = useState("");
  const [isAuthed, setIsAuthed] = useState(false);
  const [architecture, setArchitecture] = useState("standard");
  const [embedding, setEmbedding] = useState("e5_small");
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsAuthed(!!getToken());
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    if (!input.trim() || isStreaming) return;
    const question = input;
    setInput("");
    setIsStreaming(true);
    setMessages((m) => [...m, { role: "user", text: question }, { role: "bot", text: "" }]);

    try {
      await streamChat(
        question, architecture, embedding,
        (token) => {
          setMessages((m) => {
            const copy = [...m];
            copy[copy.length - 1] = { ...copy[copy.length - 1], text: copy[copy.length - 1].text + token };
            return copy;
          });
        },
        (citations) => {
          setMessages((m) => {
            const copy = [...m];
            copy[copy.length - 1] = { ...copy[copy.length - 1], citations };
            return copy;
          });
        }
      );
    } finally {
      setIsStreaming(false);
    }
  }

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto flex flex-col h-full p-4 w-full">
      <h1 className="text-xl font-semibold mb-3">Chat</h1>

      {!isAuthed && (
        <div role="status" className="flex items-start gap-2 bg-amber-50 border border-amber-200 text-amber-800 text-sm rounded-lg px-4 py-2.5 mb-3">
          <AlertCircle size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
          Anda menggunakan AkademiQ sebagai tamu. Riwayat percakapan tidak akan disimpan.
        </div>
      )}

      <div className="flex gap-2 mb-3 text-xs">
        <div>
          <label htmlFor="architecture-select" className="sr-only">Pilih arsitektur RAG</label>
          <select
            id="architecture-select"
            value={architecture}
            onChange={(e) => setArchitecture(e.target.value)}
            className="border border-slate-200 rounded px-2 py-1"
          >
            <option value="standard">Standard RAG</option>
            <option value="hyde">HyDE RAG</option>
            <option value="rerank">Re-ranking RAG</option>
          </select>
        </div>
        <div>
          <label htmlFor="embedding-select" className="sr-only">Pilih model embedding</label>
          <select
            id="embedding-select"
            value={embedding}
            onChange={(e) => setEmbedding(e.target.value)}
            className="border border-slate-200 rounded px-2 py-1"
          >
            <option value="e5_small">Multilingual-E5-small</option>
            <option value="mpnet">Paraphrase-MPNET</option>
            <option value="labse">LaBSE</option>
          </select>
        </div>
      </div>

      {/* role="log" + aria-live="polite": screen reader mengumumkan
          jawaban baru saat streaming, tanpa menginterupsi tiap token
          (aria-live="polite" menunggu jeda alami, bukan tiap huruf) */}
      <div
        ref={scrollRef}
        role="log"
        aria-live="polite"
        aria-label="Riwayat percakapan"
        className="flex-1 overflow-y-auto space-y-3 mb-3"
      >
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-lg rounded-2xl px-4 py-3 text-sm ${m.role === "user" ? "bg-blue-600 text-white" : "bg-white border border-slate-200"}`}>
              {m.text || (
                <span className="sr-only">Sedang mengetik jawaban...</span>
              )}
              {!m.text && <span aria-hidden="true">...</span>}
              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-200 flex flex-wrap gap-1">
                  {m.citations.map((c, idx) => (
                    <button
                      key={idx}
                      onClick={() => setActiveCitation(c)}
                      className="text-[11px] bg-slate-100 hover:bg-slate-200 rounded px-2 py-1"
                      title={c.chunk_text}
                      aria-label={`Lihat sumber: ${c.source_file.split("/").pop()}, halaman ${c.page_number}`}
                    >
                      📄 {c.source_file.split("/").pop()}, hal.{c.page_number}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); handleSend(); }}
        className="flex items-center gap-2 border-t border-slate-200 pt-3"
      >
        <label htmlFor="chat-input" className="sr-only">Ketik pesan Anda</label>
        <button type="button" className="text-slate-400 hover:text-slate-600 p-2" aria-label="Lampirkan file">
          <Paperclip size={18} aria-hidden="true" />
        </button>
        <input
          id="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ketik pesan Anda di sini..."
          disabled={isStreaming}
          className="flex-1 bg-slate-100 rounded-full px-4 py-2.5 text-sm outline-none disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={isStreaming || !input.trim()}
          aria-label="Kirim pesan"
          className="bg-blue-600 disabled:opacity-40 text-white rounded-full w-10 h-10 flex items-center justify-center shrink-0"
        >
          <Send size={16} aria-hidden="true" />
        </button>
      </form>

      {activeCitation && <PdfViewer citation={activeCitation} onClose={() => setActiveCitation(null)} />}
    </div>
    </AppShell>
  );
}
