#!/usr/bin/env python3
"""
Jalankan evaluasi penuh: RAGAS (9 konfigurasi x N soal) + speed
benchmark + analisis statistik, cetak rekomendasi konfigurasi optimal.

Pemakaian:
    python scripts/run_eval_all.py --dataset app/evaluation/data/eval_dataset_template.json

WAJIB pakai dataset yang SUDAH divalidasi (150 soal, minimal 2 pakar)
untuk hasil yang bisa dipertanggungjawabkan di tesis -- script ini akan
MENOLAK jalan (exit dengan error jelas) kalau dataset belum lolos
validate_dataset_composition(), supaya tidak ada risiko menjalankan
evaluasi berjam-jam di atas data yang belum siap.
"""
import argparse
import asyncio
import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.logging_config import setup_logging
from app.config import settings
from app.evaluation.dataset_schema import load_dataset, validate_dataset_composition
from app.evaluation.ragas_runner import run_full_evaluation, load_results_as_scores_by_config
from app.evaluation.speed_benchmark import run_speed_benchmark
from app.evaluation.stats_analysis import (
    compare_configurations, compute_composite_score, recommend_optimal_configuration,
)
from app.vectorstore.store_manager import StoreManager

setup_logging()
logger = logging.getLogger(__name__)

RAGAS_METRICS = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]


async def main():
    parser = argparse.ArgumentParser(description="Evaluasi penuh sembilan konfigurasi AkademiQ")
    parser.add_argument("--dataset", required=True, help="Path ke file dataset JSON")
    parser.add_argument(
        "--skip-validation", action="store_true",
        help="Lewati validasi komposisi dataset (HANYA untuk testing/development, "
             "JANGAN dipakai untuk hasil final tesis)",
    )
    parser.add_argument(
        "--speed-sample-size", type=int, default=10,
        help="Jumlah soal dipakai untuk speed benchmark (subset, tidak perlu semua)",
    )
    args = parser.parse_args()

    os.makedirs(settings.eval_results_dir, exist_ok=True)

    logger.info("Memuat dataset dari %s", args.dataset)
    questions = load_dataset(args.dataset)

    validation = validate_dataset_composition(questions)
    if not validation["is_valid"]:
        logger.error("Dataset BELUM SIAP untuk evaluasi final:")
        for issue in validation["issues"]:
            logger.error("  - %s", issue)
        if not args.skip_validation:
            logger.error(
                "Evaluasi DIBATALKAN. Gunakan --skip-validation hanya untuk uji coba "
                "teknis, bukan untuk hasil yang akan dilaporkan di tesis."
            )
            sys.exit(1)
        logger.warning("--skip-validation aktif, melanjutkan meski dataset belum lolos validasi penuh.")

    logger.info("Dataset siap: %d soal, distribusi %s", len(questions), validation["type_distribution"])

    store_manager = StoreManager()

    # --- 1. Evaluasi RAGAS ---
    ragas_output_path = os.path.join(settings.eval_results_dir, "ragas_results.json")
    logger.info("Memulai evaluasi RAGAS (%d soal x 9 konfigurasi = %d pemanggilan pipeline)...",
                len(questions), len(questions) * 9)
    await run_full_evaluation(questions, store_manager, ragas_output_path)
    logger.info("Evaluasi RAGAS selesai, hasil di %s", ragas_output_path)

    # --- 2. Speed benchmark (subset soal) ---
    speed_output_path = os.path.join(settings.eval_results_dir, "speed_results.json")
    sample_questions = [q.question for q in questions[: args.speed_sample_size]]
    logger.info("Memulai speed benchmark (%d soal sampel)...", len(sample_questions))
    speed_summaries = await run_speed_benchmark(sample_questions, store_manager, speed_output_path)
    logger.info("Speed benchmark selesai, hasil di %s", speed_output_path)

    # --- 3. Analisis statistik per metrik ---
    logger.info("Menjalankan analisis statistik...")
    comparison_results = []
    ragas_scores_per_config: dict[str, dict[str, float]] = {}

    for metric in RAGAS_METRICS:
        scores_by_config = load_results_as_scores_by_config(ragas_output_path, metric)
        result = compare_configurations(scores_by_config, metric_name=metric)
        comparison_results.append(result)

        for config_name, scores in scores_by_config.items():
            avg = sum(scores) / len(scores)
            ragas_scores_per_config.setdefault(config_name, {})[metric] = avg

        logger.info(
            "[%s] uji=%s, statistic=%.4f, p=%.6f, signifikan=%s",
            metric, result.test_used, result.statistic, result.p_value, result.is_significant,
        )

    composite_scores = compute_composite_score(ragas_scores_per_config)
    recommendation = recommend_optimal_configuration(composite_scores, comparison_results)

    # --- 4. Simpan ringkasan akhir ---
    summary_path = os.path.join(settings.eval_results_dir, "summary.json")
    summary = {
        "composite_scores": composite_scores,
        "recommendation": recommendation,
        "speed_summary": [
            {"configuration": s.configuration, "mean_seconds": s.mean_seconds, "median_seconds": s.median_seconds}
            for s in speed_summaries
        ],
        "statistical_tests": [
            {
                "metric": r.metric_name,
                "test_used": r.test_used,
                "statistic": r.statistic,
                "p_value": r.p_value,
                "is_significant": r.is_significant,
                "posthoc_test_used": r.posthoc_test_used,
            }
            for r in comparison_results
        ],
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    logger.info("=" * 60)
    logger.info("REKOMENDASI KONFIGURASI OPTIMAL: %s", recommendation["recommended_configuration"])
    logger.info("Skor komposit: %.4f", recommendation["composite_score"])
    logger.info("Didukung signifikansi statistik: %s", recommendation["statistically_justified"])
    logger.info("Ringkasan lengkap tersimpan di: %s", summary_path)
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
