import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest


def test_detects_significant_difference_when_groups_clearly_differ():
    from app.evaluation.stats_analysis import compare_configurations

    np.random.seed(1)
    scores = {
        "config_a": list(np.random.normal(0.9, 0.03, 20)),  # jelas lebih tinggi
        "config_b": list(np.random.normal(0.6, 0.03, 20)),  # jelas lebih rendah
    }
    result = compare_configurations(scores, metric_name="faithfulness")

    assert result.is_significant is True
    assert result.p_value < 0.05
    assert result.posthoc_test_used is not None


def test_no_significant_difference_when_groups_are_identical():
    from app.evaluation.stats_analysis import compare_configurations

    np.random.seed(2)
    base = list(np.random.normal(0.8, 0.05, 20))
    scores = {"config_a": base, "config_b": base.copy()}  # identik persis

    result = compare_configurations(scores, metric_name="faithfulness")
    assert result.is_significant is False
    assert result.posthoc_matrix is None  # post-hoc TIDAK dijalankan kalau tidak signifikan


def test_chooses_anova_for_normal_data():
    from app.evaluation.stats_analysis import compare_configurations

    np.random.seed(3)
    scores = {
        "a": list(np.random.normal(0.8, 0.05, 20)),
        "b": list(np.random.normal(0.75, 0.05, 20)),
    }
    result = compare_configurations(scores, metric_name="test")
    assert result.test_used == "ANOVA"


def test_chooses_kruskal_wallis_for_non_normal_data():
    from app.evaluation.stats_analysis import compare_configurations

    np.random.seed(4)
    # distribusi sangat skewed (eksponensial) -> tidak normal
    scores = {
        "a": list(np.random.exponential(0.3, 20)),
        "b": list(np.random.exponential(0.5, 20)),
    }
    result = compare_configurations(scores, metric_name="test")
    assert result.test_used == "Kruskal-Wallis"


def test_composite_score_requires_all_four_metrics():
    from app.evaluation.stats_analysis import compute_composite_score

    incomplete_scores = {
        "config_a": {"faithfulness": 0.8, "answer_relevancy": 0.7},  # kurang 2 metrik
    }
    with pytest.raises(ValueError, match="kekurangan metrik"):
        compute_composite_score(incomplete_scores)


def test_composite_score_computed_correctly():
    from app.evaluation.stats_analysis import compute_composite_score

    scores = {
        "config_a": {
            "faithfulness": 0.8, "answer_relevancy": 0.8,
            "context_recall": 0.8, "context_precision": 0.8,
        },
    }
    result = compute_composite_score(scores)
    assert result["config_a"] == pytest.approx(0.8)


def test_recommendation_flags_non_significant_results_honestly():
    """
    Test paling penting secara metodologis: sistem TIDAK BOLEH
    merekomendasikan konfigurasi terbaik seolah "terbukti unggul" kalau
    sebenarnya tidak ada perbedaan signifikan -- harus jujur menyatakan
    keterbatasan ini (statistically_justified=False).
    """
    from app.evaluation.stats_analysis import (
        compare_configurations, compute_composite_score, recommend_optimal_configuration
    )

    np.random.seed(5)
    base = list(np.random.normal(0.8, 0.05, 15))
    scores_by_metric = {"a": base, "b": [x + 0.001 for x in base]}  # nyaris identik

    comparison_results = [compare_configurations(scores_by_metric, metric_name=m) for m in
                           ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]]

    composite = {"a": 0.801, "b": 0.802}
    recommendation = recommend_optimal_configuration(composite, comparison_results)

    assert recommendation["statistically_justified"] is False
    assert "bukan berbasis signifikansi statistik" in recommendation["note"]
