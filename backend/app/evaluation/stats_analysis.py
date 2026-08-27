"""
Analisis statistik untuk membandingkan performa sembilan konfigurasi
sistem RAG (3 arsitektur x 3 model embedding) berdasarkan skor RAGAS.

Prosedur mengikuti Bab III skripsi/tesis:
1. Uji normalitas (Shapiro-Wilk) per grup/konfigurasi
2. Uji perbedaan: ANOVA satu arah (data normal) atau Kruskal-Wallis
   (data tidak normal) -- dipilih OTOMATIS berdasarkan hasil (1)
3. Uji post-hoc (kalau hasil (2) signifikan, p < 0.05): Tukey HSD
   (parametrik) atau Dunn dengan koreksi Bonferroni (non-parametrik)

Didesain untuk dijalankan terpisah per metrik RAGAS (Faithfulness,
Answer Relevancy, Context Recall, Context Precision), sesuai desain
penelitian yang memisahkan analisis per dimensi evaluasi.
"""
from dataclasses import dataclass, field
import numpy as np
from scipy import stats
import scikit_posthocs as sp


@dataclass
class NormalityResult:
    configuration: str
    statistic: float
    p_value: float
    is_normal: bool  # p_value > 0.05


@dataclass
class GroupComparisonResult:
    metric_name: str
    test_used: str  # "ANOVA" atau "Kruskal-Wallis"
    statistic: float
    p_value: float
    is_significant: bool  # p_value < 0.05
    normality_per_group: list[NormalityResult] = field(default_factory=list)
    posthoc_matrix: "np.ndarray | None" = None
    posthoc_test_used: str | None = None
    configuration_labels: list[str] = field(default_factory=list)


ALPHA = 0.05


def test_normality_per_group(scores_by_config: dict[str, list[float]]) -> list[NormalityResult]:
    """
    Shapiro-Wilk per konfigurasi. Cocok untuk sampel kecil (n < 50),
    sesuai skala tipikal jumlah pertanyaan evaluasi per konfigurasi
    pada penelitian ini.
    """
    results = []
    for config_name, scores in scores_by_config.items():
        scores_arr = np.array(scores)
        if len(scores_arr) < 3:
            # Shapiro-Wilk butuh minimal 3 sampel -- tandai eksplisit,
            # jangan diam-diam skip (silent failure berbahaya untuk tesis)
            results.append(NormalityResult(config_name, float("nan"), float("nan"), False))
            continue
        statistic, p_value = stats.shapiro(scores_arr)
        results.append(NormalityResult(config_name, float(statistic), float(p_value), bool(p_value > ALPHA)))
    return results


def compare_configurations(
    scores_by_config: dict[str, list[float]],
    metric_name: str,
) -> GroupComparisonResult:
    """
    scores_by_config: dict {nama_konfigurasi: [skor1, skor2, ...]}
    contoh key: "standard+e5_small", "hyde+mpnet", dst (9 total).

    Pemilihan uji OTOMATIS: ANOVA kalau SEMUA grup terdistribusi
    normal, Kruskal-Wallis kalau ADA SATU SAJA grup yang tidak normal
    -- ini pendekatan konservatif yang umum dipakai (bukan cuma cek
    rata-rata p-value semua grup).
    """
    normality_results = test_normality_per_group(scores_by_config)
    all_normal = all(r.is_normal for r in normality_results)

    labels = list(scores_by_config.keys())
    groups = [np.array(scores_by_config[label]) for label in labels]

    if all_normal:
        statistic, p_value = stats.f_oneway(*groups)
        test_used = "ANOVA"
    else:
        statistic, p_value = stats.kruskal(*groups)
        test_used = "Kruskal-Wallis"

    is_significant = bool(p_value < ALPHA)

    posthoc_matrix = None
    posthoc_test_used = None
    if is_significant:
        # Susun jadi format long-form yang dibutuhkan scikit-posthocs
        all_values = np.concatenate(groups)
        all_labels = np.concatenate([[label] * len(scores_by_config[label]) for label in labels])

        if all_normal:
            # Tukey HSD via statsmodels
            from statsmodels.stats.multicomp import pairwise_tukeyhsd
            tukey_result = pairwise_tukeyhsd(all_values, all_labels, alpha=ALPHA)
            posthoc_matrix = tukey_result  # simpan objek lengkap, punya .summary()
            posthoc_test_used = "Tukey HSD"
        else:
            posthoc_matrix = sp.posthoc_dunn(
                [scores_by_config[label] for label in labels],
                p_adjust="bonferroni",
            )
            posthoc_matrix.index = labels
            posthoc_matrix.columns = labels
            posthoc_test_used = "Dunn (koreksi Bonferroni)"

    return GroupComparisonResult(
        metric_name=metric_name,
        test_used=test_used,
        statistic=float(statistic),
        p_value=float(p_value),
        is_significant=is_significant,
        normality_per_group=normality_results,
        posthoc_matrix=posthoc_matrix,
        posthoc_test_used=posthoc_test_used,
        configuration_labels=labels,
    )


def compute_composite_score(ragas_scores: dict[str, dict[str, float]]) -> dict[str, float]:
    """
    ragas_scores: dict {nama_konfigurasi: {"faithfulness": x, "answer_relevancy": y,
                                             "context_recall": z, "context_precision": w}}
    Skor komposit = rata-rata bobot sama (25% masing-masing), sesuai
    Bab III (Penentuan Konfigurasi Optimal).
    """
    composite = {}
    required_keys = {"faithfulness", "answer_relevancy", "context_recall", "context_precision"}
    for config_name, metrics in ragas_scores.items():
        missing = required_keys - set(metrics.keys())
        if missing:
            raise ValueError(f"Konfigurasi '{config_name}' kekurangan metrik: {missing}")
        composite[config_name] = sum(metrics[k] for k in required_keys) / 4
    return composite


def recommend_optimal_configuration(
    composite_scores: dict[str, float],
    comparison_results: list[GroupComparisonResult],
) -> dict:
    """
    Rekomendasi = skor komposit tertinggi YANG SECARA STATISTIK berbeda
    signifikan dari setidaknya satu konfigurasi lain (bukan cuma
    "angka tertinggi" tanpa pertimbangan signifikansi -- ini poin
    metodologis penting untuk defensif di sidang).
    """
    ranked = sorted(composite_scores.items(), key=lambda x: x[1], reverse=True)
    top_config, top_score = ranked[0]

    any_significant = any(r.is_significant for r in comparison_results)

    if not any_significant:
        return {
            "recommended_configuration": top_config,
            "composite_score": top_score,
            "statistically_justified": False,
            "note": (
                "Skor komposit tertinggi dicapai oleh "
                f"'{top_config}', namun TIDAK ADA metrik RAGAS yang menunjukkan "
                "perbedaan signifikan (p < 0.05) antar konfigurasi. Rekomendasi "
                "ini bersifat deskriptif, bukan berbasis signifikansi statistik -- "
                "nyatakan keterbatasan ini secara eksplisit di bab pembahasan."
            ),
        }

    return {
        "recommended_configuration": top_config,
        "composite_score": top_score,
        "statistically_justified": True,
        "note": f"Konfigurasi '{top_config}' direkomendasikan berdasarkan skor komposit tertinggi, didukung oleh perbedaan signifikan pada minimal satu metrik RAGAS.",
    }
