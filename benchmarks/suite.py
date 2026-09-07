"""Creativity benchmark suite for measuring search signals across varied problem types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
from howlcreate.engine.dedup import ConceptDeduplicator
from howlcreate.engine.pipeline import CreativePipeline, PipelineConfig
from howlcreate.models.run import RunRecord
from howlcreate.providers.base import BaseProvider


BENCHMARK_PROBLEMS = [
    {
        "id": "eng-01",
        "category": "engineering",
        "problem": "How to design an embedded database engine that guarantees zero data loss during sudden power failure without using battery-backed RAM?",
    },
    {
        "id": "prod-01",
        "category": "product_design",
        "problem": "How to design a code review interface that makes reading 1,000 lines of complex logic as intuitive as reading a children's book?",
    },
    {
        "id": "org-01",
        "category": "organizational",
        "problem": "How can 50 completely anonymous engineers make binding architectural decisions without managers or voting deadlocks?",
    },
    {
        "id": "auto-01",
        "category": "automation",
        "problem": "How can a system automatically repair complex race conditions in concurrent Go code without manual human intervention?",
    },
    {
        "id": "cost-01",
        "category": "cost_reduction",
        "problem": "How can an AI agent platform reduce LLM inference costs by 95% while retaining 99% reasoning quality?",
    },
    {
        "id": "arch-01",
        "category": "software_architecture",
        "problem": "How to design a state synchronization protocol between mobile apps that works over high-latency intermittent peer-to-peer radio?",
    },
    {
        "id": "debug-01",
        "category": "debugging",
        "problem": "How to isolate non-reproducible memory corruption bugs that only trigger after 3 weeks of continuous execution?",
    },
    {
        "id": "remote-01",
        "category": "remote_work",
        "problem": "How could the Howl ecosystem create meaningful remote-work opportunities rather than merely being software about remote work?",
    },
    {
        "id": "access-01",
        "category": "accessibility",
        "problem": "How can a blind software engineer navigate and edit complex multi-column interactive terminal UIs at the speed of a sighted senior developer?",
    },
    {
        "id": "rel-01",
        "category": "reliability",
        "problem": "How to achieve 99.999% availability on unreliable consumer hardware nodes that disconnect without warning?",
    },
    {
        "id": "sec-01",
        "category": "security",
        "problem": "How to allow untrusted third-party code plugins to process private customer documents without leaking information across network channels?",
    },
    {
        "id": "extreme-01",
        "category": "impossible_constraints",
        "problem": "Build an operating system with zero bytes of persistent disk storage where all computation survives power cycles.",
    },
]


@dataclass
class BenchmarkMetrics:
    """Quantitative creativity signals for a run."""
    problem_id: str
    category: str
    total_concepts: int
    distinct_clusters: int
    duplicate_rate: float
    max_lineage_depth: int
    synthesis_count: int
    average_novelty: float
    average_feasibility: float
    finalists_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "category": self.category,
            "total_concepts": self.total_concepts,
            "distinct_clusters": self.distinct_clusters,
            "duplicate_rate": round(self.duplicate_rate, 3),
            "max_lineage_depth": self.max_lineage_depth,
            "synthesis_count": self.synthesis_count,
            "average_novelty": round(self.average_novelty, 3),
            "average_feasibility": round(self.average_feasibility, 3),
            "finalists_count": self.finalists_count,
        }


def calculate_lineage_depth(record: RunRecord) -> int:
    """Calculate the maximum derivation depth in the concept DAG."""
    depths: Dict[str, int] = {}

    def get_depth(node_id: str) -> int:
        if node_id in depths:
            return depths[node_id]
        parents = [e.parent_id for e in record.graph.edges if e.child_id == node_id]
        if not parents:
            depths[node_id] = 1
            return 1
        d = 1 + max(get_depth(p) for p in parents)
        depths[node_id] = d
        return d

    if not record.graph.nodes:
        return 0
    return max(get_depth(n) for n in record.graph.nodes)


def evaluate_run_signals(problem_id: str, category: str, record: RunRecord) -> BenchmarkMetrics:
    """Extract measurable signals from a completed creative search."""
    ideas = list(record.graph.nodes.values())
    total = len(ideas)

    dedup = ConceptDeduplicator(similarity_threshold=0.52)
    clusters, _ = dedup.cluster_ideas(ideas)
    cluster_count = len(clusters)

    # Duplicate rate: fraction of ideas that share a cluster with another idea
    multi_member_count = sum(len(m) for m in clusters.values() if len(m) > 1)
    dup_rate = (multi_member_count / total) if total > 0 else 0.0

    lineage_depth = calculate_lineage_depth(record)
    synthesis_count = sum(1 for i in ideas if i.operator_used in ["synthesis", "forced_combination"] or len(i.parent_ids) > 1)

    novelty_scores = []
    feasibility_scores = []
    for idea in ideas:
        for ev in idea.evaluations:
            if "novelty" in ev.scores:
                novelty_scores.append(ev.scores["novelty"].score)
            if "feasibility" in ev.scores:
                feasibility_scores.append(ev.scores["feasibility"].score)

    avg_novelty = sum(novelty_scores) / len(novelty_scores) if novelty_scores else 0.0
    avg_feasibility = sum(feasibility_scores) / len(feasibility_scores) if feasibility_scores else 0.0

    return BenchmarkMetrics(
        problem_id=problem_id,
        category=category,
        total_concepts=total,
        distinct_clusters=cluster_count,
        duplicate_rate=dup_rate,
        max_lineage_depth=lineage_depth,
        synthesis_count=synthesis_count,
        average_novelty=avg_novelty,
        average_feasibility=avg_feasibility,
        finalists_count=len(record.finalist_ids),
    )


def run_benchmark_suite(provider: BaseProvider, limit: int = 3) -> List[BenchmarkMetrics]:
    """Execute benchmark problems through the pipeline and return metric signals."""
    results: List[BenchmarkMetrics] = []
    pipeline = CreativePipeline(config=PipelineConfig(top_n=3, save_run=False))

    for item in BENCHMARK_PROBLEMS[:limit]:
        record = pipeline.execute(item["problem"], provider=provider)
        metrics = evaluate_run_signals(item["id"], item["category"], record)
        results.append(metrics)

    return results
