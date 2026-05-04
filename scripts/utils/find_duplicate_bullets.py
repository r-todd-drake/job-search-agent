# scripts/utils/find_duplicate_bullets.py
# Identifies same or near-duplicate bullets across the experience library.
#
# Usage:
#   python -m scripts.utils.find_duplicate_bullets
#   python -m scripts.utils.find_duplicate_bullets --threshold 90

import os
import json
import argparse
from collections import defaultdict
from datetime import datetime
from rapidfuzz import fuzz as _fuzz

LIBRARY_PATH = "data/experience_library/experience_library.json"
OUTPUT_DIR = "outputs"


def _extract_bullets(library: dict) -> list:
    """Flatten employers[].bullets[] into a single list, adding 'employer' key to each bullet."""
    result = []
    for employer in library.get("employers", []):
        name = employer["name"]
        for bullet in employer.get("bullets", []):
            result.append({
                "id": bullet["id"],
                "theme": bullet["theme"],
                "text": bullet["text"],
                "employer": name,
            })
    return result


def _compute_pairs(bullets: list, threshold: float) -> list:
    """Return list of (bullet_a, bullet_b, score) for all pairs at or above threshold."""
    pairs = []
    for i in range(len(bullets)):
        for j in range(i + 1, len(bullets)):
            score = _fuzz.token_sort_ratio(bullets[i]["text"], bullets[j]["text"])
            if score >= threshold:
                pairs.append((bullets[i], bullets[j], float(score)))
    return pairs


def _build_clusters(bullets: list, pairs: list) -> list:
    """Union-find clustering over matched pairs. Returns cluster dicts sorted by max_score desc."""
    parent = {b["id"]: b["id"] for b in bullets}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    pair_index = {}
    for bullet_a, bullet_b, score in pairs:
        union(bullet_a["id"], bullet_b["id"])
        pair_index[(bullet_a["id"], bullet_b["id"])] = score

    groups = defaultdict(list)
    for b in bullets:
        groups[find(b["id"])].append(b)

    clusters = []
    for members in groups.values():
        if len(members) < 2:
            continue
        ids = {m["id"] for m in members}
        cluster_pairs = [
            (id_a, id_b, score)
            for (id_a, id_b), score in pair_index.items()
            if id_a in ids and id_b in ids
        ]
        max_score = max((s for _, _, s in cluster_pairs), default=0.0)
        clusters.append({
            "bullets": members,
            "pairs": cluster_pairs,
            "max_score": max_score,
        })

    return sorted(clusters, key=lambda c: c["max_score"], reverse=True)


def find_duplicate_clusters(bullets: list, threshold: float = 85.0) -> list:
    """Find clusters of duplicate or near-duplicate bullets.

    Pure function -- no file I/O. Injectable inputs for testability.

    Args:
        bullets: list of dicts with keys: id, theme, text, employer
        threshold: minimum fuzz.token_sort_ratio score to consider a match (0-100)

    Returns:
        list of cluster dicts, each containing:
            bullets: list of matching bullet dicts
            pairs:   list of (id_a, id_b, score) tuples for each matched pair
            max_score: highest pairwise score in the cluster
    """
    if len(bullets) < 2:
        return []
    pairs = _compute_pairs(bullets, threshold)
    if not pairs:
        return []
    return _build_clusters(bullets, pairs)


def format_cluster_report(clusters: list) -> str:
    """Format clusters for human-readable output. (Stub — implemented in later task.)"""
    pass
