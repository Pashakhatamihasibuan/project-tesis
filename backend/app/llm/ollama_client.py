"""
Client untuk Ollama (LLM lokal, Aya 23 8B).

CATATAN: butuh Ollama berjalan di mesin yang sama (`ollama serve`) dan
model sudah di-pull (`ollama pull aya:8b`) sebelum kode ini bisa
dipakai. Tidak jalan di sandbox ini karena Ollama tidak terinstall,
tapi ini yang akan dipakai saat deploy di laptop/PC pengembangan.
"""
import json
import httpx

from app.config import settings


async def generate_stream(prompt: str, system_prompt: str = ""):
    """
    Async generator yang yield token demi token (untuk SSE streaming
    ke frontend). Dipakai di api/chat.py.
    """
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", f"{settings.ollama_base_url}/api/generate", json=payload) as response:
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                data = json.loads(line)
                if "response" in data:
                    yield data["response"]
                if data.get("done"):
                    break


async def generate_once(prompt: str, system_prompt: str = "") -> str:
    """Versi non-streaming, dipakai HyDE untuk generate dokumen hipotetis."""
    chunks = []
    async for token in generate_stream(prompt, system_prompt):
        chunks.append(token)
    return "".join(chunks)
