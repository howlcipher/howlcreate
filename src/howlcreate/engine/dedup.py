"""Deduplication and semantic clustering for concept pools."""

from __future__ import annotations

from collections import Counter
import math
import re
from typing import Dict, List, Tuple
from howlcreate.models.idea import Idea


def _tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into clean words."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    stopwords = {
        "a", "an", "the", "and", "or", "but", "if", "then", "of", "to", "in",
        "for", "on", "with", "by", "at", "from", "is", "are", "was", "were",
        "be", "been", "that", "this", "which", "it", "as", "how", "what",
        "on", "pr", "prs", "via"
    }
    return [w for w in cleaned.split() if len(w) > 2 and w not in stopwords]


def compute_similarity(idea_a: Idea, idea_b: Idea) -> float:
    """Compute structural similarity between two ideas based on titles, mechanisms, and descriptions."""
    text_a = f"{idea_a.title} {idea_a.core_mechanism} {idea_a.description}"
    text_b = f"{idea_b.title} {idea_b.core_mechanism} {idea_b.description}"

    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)

    if not tokens_a or not tokens_b:
        return 0.0

    set_a = set(tokens_a)
    set_b = set(tokens_b)

    # Word unigram Jaccard
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    unigram_jaccard = intersection / union if union > 0 else 0.0

    # Token cosine similarity
    counter_a = Counter(tokens_a)
    counter_b = Counter(tokens_b)

    dot_product = sum(counter_a[t] * counter_b[t] for t in counter_a if t in counter_b)
    mag_a = math.sqrt(sum(v * v for v in counter_a.values()))
    mag_b = math.sqrt(sum(v * v for v in counter_b.values()))
    cosine = (dot_product / (mag_a * mag_b)) if (mag_a * mag_b) > 0 else 0.0

    # Bigram Jaccard if tokens are sufficiently long
    bigrams_a = {f"{tokens_a[i]}_{tokens_a[i+1]}" for i in range(len(tokens_a) - 1)}
    bigrams_b = {f"{tokens_b[i]}_{tokens_b[i+1]}" for i in range(len(tokens_b) - 1)}
    bg_inter = len(bigrams_a.intersection(bigrams_b))
    bg_union = len(bigrams_a.union(bigrams_b))
    bg_jaccard = bg_inter / bg_union if bg_union > 0 else 0.0

    return round(0.45 * unigram_jaccard + 0.45 * cosine + 0.10 * bg_jaccard, 4)


class ConceptDeduplicator:
    """Detects near-duplicates, clusters ideas, and identifies unique outliers."""

    def __init__(self, similarity_threshold: float = 0.40):
        self.similarity_threshold = similarity_threshold

    def cluster_ideas(self, ideas: List[Idea]) -> Tuple[Dict[str, List[Idea]], List[Idea]]:
        """Cluster ideas by similarity.

        Returns:
            clusters: dict mapping cluster_id -> list of ideas in that cluster
            outliers: list of ideas with low similarity to all others (high distinctness)
        """
        if not ideas:
            return {}, []

        clusters: Dict[str, List[Idea]] = {}
        assigned_cluster: Dict[str, str] = {}
        cluster_idx = 1

        for i, idea in enumerate(ideas):
            if idea.id in assigned_cluster:
                continue

            current_cluster_id = f"cluster-{cluster_idx}"
            cluster_members = [idea]
            assigned_cluster[idea.id] = current_cluster_id
            idea.cluster_id = current_cluster_id

            for other in ideas[i + 1:]:
                if other.id in assigned_cluster:
                    continue

                sim = compute_similarity(idea, other)
                if sim >= self.similarity_threshold:
                    cluster_members.append(other)
                    assigned_cluster[other.id] = current_cluster_id
                    other.cluster_id = current_cluster_id

            clusters[current_cluster_id] = cluster_members
            cluster_idx += 1

        # Identify outliers (clusters with exactly 1 member that have low max similarity)
        outliers: List[Idea] = []
        for cluster_id, members in clusters.items():
            if len(members) == 1:
                target = members[0]
                max_sim = max(
                    (compute_similarity(target, other) for other in ideas if other.id != target.id),
                    default=0.0
                )
                if max_sim < (self.similarity_threshold * 0.75):
                    outliers.append(target)

        return clusters, outliers
