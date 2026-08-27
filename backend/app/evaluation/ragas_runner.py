"""
Runner evaluasi RAGAS untuk sembilan konfigurasi sistem (3 arsitektur
RAG x 3 model embedding), sesuai Bab III.D dan III.E.2 tesis.

DESAIN METODOLOGIS PENTING -- baca sebelum mengubah kode ini:

1. Judge LLM (penilai) memakai Ollama LOKAL (model sama dengan
   generator jawaban, Aya 23 8B), BUKAN OpenAI/API berbayar. Ini
   konsisten dengan novelty penelitian ("local RAG, tanpa API
   berbayar"). Trade-off yang harus diakui di bab keterbatasan: LLM
   judge lokal berukuran 8B kemungkinan kurang presisi dibanding
   GPT-4 sebagai judge (yang jadi default RAGAS di banyak penelitian
   lain) -- ini keterbatasan yang harus dinyatakan eksplisit, bukan
   disembunyikan.

2. Embedding untuk metrik answer_relevancy SENGAJA di-FIX ke satu
   model (default: e5_small, lihat settings.ragas_embedding_model),
   TIDAK ikut berganti sesuai embedding yang sedang diuji pada
   konfigurasi tersebut. Alasan: answer_relevancy dihitung dari cosine
   similarity antara pertanyaan asli dan pertanyaan hasil generate-balik
   dari jawaban. Kalau embedding penilai ini ikut berubah sesuai
   embedding yang diuji, hasil metrik jadi bias/confounded -- sistem
   seolah "menilai dirinya sendiri" dengan alat ukur yang berbeda-beda
   per konfigurasi, sehingga perbandingan antar konfigurasi tidak adil.
   Ini adalah keputusan desain yang WAJIB disebutkan di Bab III sebagai
   bagian dari kontrol validitas internal eksperimen.
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict

from app.config import settings
from app.evaluation.dataset_schema import EvalQuestion
from app.rag.pipeline_factory import get_pipeline, get_embedder
from app.vectorstore.store_manager import StoreManager

logger = logging.getLogger(__name__)


@dataclass
class SingleEvalResult:
    question_id: str
    configuration: str
    question: str
    generated_answer: str
    ground_truth: str
    retrieved_contexts: list[str]
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_recall: float | None = None
    context_precision: float | None = None
    latency_seconds: float | None = None
    error: str | None = None


async def _run_single_pipeline(
    question: EvalQuestion,
    architecture: str,
    embedding_key: str,
    store_manager: StoreManager,
) -> tuple[str, list[str], float]:
    """
    Jalankan satu pipeline RAG untuk satu pertanyaan. Mengembalikan
    (jawaban lengkap, daftar konteks yang diambil, waktu tempuh detik).

    PENTING: retrieval pada evaluasi ini murni SEMANTIK (TurboVec saja),
    TANPA BM25 hybrid search -- sesuai cakupan penelitian (Bab I.F.4)
    yang membatasi sembilan konfigurasi inti hanya menguji variabel
    arsitektur RAG dan model embedding, bukan strategi retrieval
    tambahan seperti hybrid search (itu fitur pelengkap di luar cakupan).
    """
    pipeline_fn = get_pipeline(architecture)
    embedder = get_embedder(embedding_key, use_dummy=False)

    start = time.perf_counter()
    answer_parts = []
    contexts = []

    async for event in pipeline_fn(
        question.question, embedder, store_manager,
        top_k=settings.top_k_default, use_hybrid=False,
        # use_hybrid=False WAJIB untuk sembilan konfigurasi inti --
        # lihat docstring modul ini dan hybrid_search.py.
    ):
        if event["type"] == "token":
            answer_parts.append(event["content"])
        elif event["type"] == "citations":
            contexts = [c["chunk_text"] for c in event["content"]]

    elapsed = time.perf_counter() - start
    return "".join(answer_parts), contexts, elapsed


def _compute_ragas_metrics(
    question: str,
    answer: str,
    contexts: list[str],
    ground_truth: str,
    judge_llm,
    fixed_embeddings,
) -> dict[str, float]:
    """
    Hitung 4 metrik RAGAS untuk satu (pertanyaan, jawaban, konteks).

    Menggunakan ragas==0.1.21 API (dipin di requirements.txt --
    lihat catatan di sana soal bug dependency versi lebih baru).
    """
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision

    eval_dataset = Dataset.from_dict({
        "question": [question],
        "answer": [answer],
        "contexts": [contexts],
        "ground_truth": [ground_truth],
    })

    result = evaluate(
        eval_dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=judge_llm,
        embeddings=fixed_embeddings,
    )

    df = result.to_pandas()
    return {
        "faithfulness": float(df["faithfulness"].iloc[0]),
        "answer_relevancy": float(df["answer_relevancy"].iloc[0]),
        "context_recall": float(df["context_recall"].iloc[0]),
        "context_precision": float(df["context_precision"].iloc[0]),
    }


def _build_judge_llm():
    """
    LLM judge lokal via Ollama, dibungkus wrapper LangChain yang
    dipahami RAGAS. Lihat docstring modul ini soal rasionalnya.
    """
    from langchain_community.chat_models import ChatOllama
    from ragas.llms import LangchainLLMWrapper

    chat_model = ChatOllama(model=settings.ragas_judge_model, base_url=settings.ollama_base_url)
    return LangchainLLMWrapper(chat_model)


def _build_fixed_embeddings():
    """
    Embedding TETAP (tidak ikut berubah per konfigurasi) untuk metrik
    answer_relevancy. Lihat docstring modul ini poin 2.
    """
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from langchain_community.embeddings import HuggingFaceEmbeddings

    model_name = settings.embedding_models[settings.ragas_embedding_model]
    hf_embeddings = HuggingFaceEmbeddings(model_name=model_name)
    return LangchainEmbeddingsWrapper(hf_embeddings)


async def run_full_evaluation(
    questions: list[EvalQuestion],
    store_manager: StoreManager,
    output_path: str,
) -> list[SingleEvalResult]:
    """
    Jalankan seluruh dataset pertanyaan terhadap sembilan konfigurasi.
    Total pemanggilan pipeline = len(questions) x 9.

    Hasil ditulis INKREMENTAL ke output_path (append per konfigurasi
    selesai) -- kalau proses terhenti di tengah jalan (mati listrik,
    Ollama crash, dsb), hasil yang sudah didapat TIDAK hilang.
    """
    judge_llm = _build_judge_llm()
    fixed_embeddings = _build_fixed_embeddings()

    all_results: list[SingleEvalResult] = []

    for config in settings.all_configurations:
        arch, emb = config["architecture"], config["embedding"]
        config_name = f"{arch}+{emb}"
        logger.info("Mulai evaluasi konfigurasi: %s (%d soal)", config_name, len(questions))

        for question in questions:
            try:
                answer, contexts, latency = await _run_single_pipeline(question, arch, emb, store_manager)

                if not contexts:
                    logger.warning(
                        "Konfigurasi %s, soal %s: tidak ada konteks ter-retrieve. "
                        "Metrik context_precision/recall akan tidak valid untuk entri ini.",
                        config_name, question.id,
                    )

                metrics = _compute_ragas_metrics(
                    question.question, answer, contexts, question.ground_truth,
                    judge_llm, fixed_embeddings,
                )

                result = SingleEvalResult(
                    question_id=question.id,
                    configuration=config_name,
                    question=question.question,
                    generated_answer=answer,
                    ground_truth=question.ground_truth,
                    retrieved_contexts=contexts,
                    latency_seconds=latency,
                    **metrics,
                )
            except Exception as e:
                logger.exception("Gagal evaluasi soal %s pada konfigurasi %s", question.id, config_name)
                result = SingleEvalResult(
                    question_id=question.id,
                    configuration=config_name,
                    question=question.question,
                    generated_answer="",
                    ground_truth=question.ground_truth,
                    retrieved_contexts=[],
                    error=str(e),
                )

            all_results.append(result)

        # simpan progres setelah tiap konfigurasi selesai, bukan
        # menunggu semua 9 x N selesai baru ditulis sekali
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in all_results], f, ensure_ascii=False, indent=2)
        logger.info("Progres tersimpan ke %s (%d hasil sejauh ini)", output_path, len(all_results))

    return all_results


def load_results_as_scores_by_config(results_path: str, metric: str) -> dict[str, list[float]]:
    """
    Baca file hasil evaluasi, kelompokkan skor satu metrik per
    konfigurasi -- format yang dibutuhkan langsung oleh
    stats_analysis.compare_configurations().
    """
    with open(results_path, "r", encoding="utf-8") as f:
        raw_results = json.load(f)

    scores_by_config: dict[str, list[float]] = {}
    for r in raw_results:
        if r.get("error") is not None:
            continue  # entri gagal tidak dihitung dalam analisis statistik
        value = r.get(metric)
        if value is None:
            continue
        scores_by_config.setdefault(r["configuration"], []).append(value)

    return scores_by_config
