"""
Benchmark kecepatan sembilan konfigurasi -- metrik pelengkap di luar
empat metrik RAGAS (Bab I.F.4 poin 7 Spesifikasi Produk). Mengukur
BUKAN cuma total waktu, tapi breakdown per tahap (embedding query,
retrieval, generation), supaya bab pembahasan bisa menjelaskan SUMBER
perbedaan kecepatan antar arsitektur -- bukan cuma melaporkan angka.
"""
import asyncio
import json
import logging
import statistics
import time
from dataclasses import dataclass, asdict

from app.config import settings
from app.rag.pipeline_factory import get_pipeline, get_embedder
from app.vectorstore.store_manager import StoreManager
from app.utils.timer import TimingCollector

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkRun:
    configuration: str
    question: str
    total_seconds: float
    stage_breakdown: dict


@dataclass
class ConfigurationSummary:
    configuration: str
    n_runs: int
    mean_seconds: float
    median_seconds: float
    stdev_seconds: float
    min_seconds: float
    max_seconds: float


async def _timed_single_run(question: str, architecture: str, embedding_key: str, store_manager: StoreManager) -> BenchmarkRun:
    """
    Catatan jujur soal keterbatasan breakdown per tahap: karena
    pipeline RAG (standard_rag.py dkk) menggabungkan retrieval dan
    generation dalam satu alur `async for` yang streaming, breakdown
    presisi murni "waktu retrieval saja" vs "waktu generation saja"
    memerlukan instrumentasi LANGSUNG di dalam pipeline (menyisipkan
    TimingCollector ke standard_rag.py/hyde_rag.py/rerank_rag.py),
    bukan diukur dari luar seperti fungsi ini. Fungsi ini mengukur
    total end-to-end yang akurat, TAPI breakdown tahap yang disediakan
    di bawah adalah PERKIRAAN berbasis pemisahan retrieval vs streaming
    token pertama -- nyatakan keterbatasan ini di bab metode kalau
    dipakai apa adanya.
    """
    pipeline_fn = get_pipeline(architecture)
    embedder = get_embedder(embedding_key, use_dummy=False)

    collector = TimingCollector()
    first_token_time = None
    start = time.perf_counter()

    with collector.stage("total_end_to_end"):
        async for event in pipeline_fn(question, embedder, store_manager, use_hybrid=False):
            if event["type"] == "token" and first_token_time is None:
                first_token_time = time.perf_counter() - start

    breakdown = collector.as_dict()
    if first_token_time is not None:
        breakdown["time_to_first_token"] = round(first_token_time, 4)

    return BenchmarkRun(
        configuration=f"{architecture}+{embedding_key}",
        question=question,
        total_seconds=collector.total_seconds,
        stage_breakdown=breakdown,
    )


async def run_speed_benchmark(
    questions: list[str],
    store_manager: StoreManager,
    output_path: str,
    runs_per_question: int = 1,
) -> list[ConfigurationSummary]:
    """
    questions: sampel pertanyaan (TIDAK perlu seluruh 150 -- cukup
    subset representatif, misal 10-15 soal, karena tujuannya mengukur
    KARAKTERISTIK KECEPATAN tiap konfigurasi, bukan akurasi jawabannya
    -- akurasi sudah diukur terpisah oleh RAGAS di ragas_runner.py.
    """
    all_runs: list[BenchmarkRun] = []

    for config in settings.all_configurations:
        arch, emb = config["architecture"], config["embedding"]
        config_name = f"{arch}+{emb}"
        logger.info("Benchmark kecepatan: %s", config_name)

        for question in questions:
            for _ in range(runs_per_question):
                run = await _timed_single_run(question, arch, emb, store_manager)
                all_runs.append(run)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in all_runs], f, ensure_ascii=False, indent=2)

    return summarize_benchmark(all_runs)


def summarize_benchmark(runs: list[BenchmarkRun]) -> list[ConfigurationSummary]:
    grouped: dict[str, list[float]] = {}
    for run in runs:
        grouped.setdefault(run.configuration, []).append(run.total_seconds)

    summaries = []
    for config_name, durations in grouped.items():
        summaries.append(
            ConfigurationSummary(
                configuration=config_name,
                n_runs=len(durations),
                mean_seconds=round(statistics.mean(durations), 4),
                median_seconds=round(statistics.median(durations), 4),
                stdev_seconds=round(statistics.stdev(durations), 4) if len(durations) > 1 else 0.0,
                min_seconds=round(min(durations), 4),
                max_seconds=round(max(durations), 4),
            )
        )
    return sorted(summaries, key=lambda s: s.mean_seconds)
