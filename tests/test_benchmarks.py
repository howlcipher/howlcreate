"""Tests for creativity benchmark suite and metric signal extraction."""

from benchmarks.suite import BENCHMARK_PROBLEMS, run_benchmark_suite
from howlcreate.providers.deterministic import DeterministicProvider


def test_benchmark_problems_catalog():
    assert len(BENCHMARK_PROBLEMS) == 12
    categories = {p["category"] for p in BENCHMARK_PROBLEMS}
    assert "remote_work" in categories
    assert "impossible_constraints" in categories
    assert "software_architecture" in categories


def test_benchmark_suite_execution():
    provider = DeterministicProvider()
    results = run_benchmark_suite(provider, limit=2)

    assert len(results) == 2
    for r in results:
        assert r.total_concepts > 5
        assert r.distinct_clusters >= 1
        assert r.max_lineage_depth >= 2
        assert r.finalists_count >= 1
        assert 0.0 <= r.average_novelty <= 1.0
        assert 0.0 <= r.average_feasibility <= 1.0
