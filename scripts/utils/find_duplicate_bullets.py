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


def format_cluster_report(clusters: list, threshold: float, total_bullets: int) -> str:
    """Format duplicate clusters as a human-readable report string."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "=" * 60,
        "DUPLICATE BULLET REPORT",
        f"Generated: {now}",
        f"Threshold: {threshold:.0f}%",
        f"Total bullets scanned: {total_bullets}",
        f"Duplicate clusters found: {len(clusters)}",
        "=" * 60,
        "",
    ]

    if not clusters:
        lines.append("No duplicate clusters found at this threshold.")
        return "\n".join(lines)

    for i, cluster in enumerate(clusters, start=1):
        lines += [
            f"Cluster {i}  (max similarity: {cluster['max_score']:.0f}%)",
            "-" * 40,
        ]
        for bullet in cluster["bullets"]:
            lines += [
                f"  [{bullet['id']}] {bullet['employer']} | Theme: {bullet['theme']}",
                f"  {bullet['text']}",
                "",
            ]
        if cluster["pairs"]:
            lines.append("  Pairwise scores:")
            for id_a, id_b, score in cluster["pairs"]:
                lines.append(f"    {id_a} -- {id_b}: {score:.0f}%")
        lines += ["", "---", ""]

    return "\n".join(lines)


def main(library_path: str, output_dir: str, threshold: float) -> None:
    print("=" * 60)
    print("DUPLICATE BULLET FINDER")
    print("=" * 60)

    with open(library_path, encoding="utf-8") as f:
        library = json.load(f)

    bullets = _extract_bullets(library)
    total = len(bullets)
    print(f"  Bullets loaded: {total}")
    print(f"  Threshold: {threshold:.0f}%")
    print("  Scanning for duplicates...")

    clusters = find_duplicate_clusters(bullets, threshold=threshold)
    print(f"  Clusters found: {len(clusters)}")

    report = format_cluster_report(clusters, threshold=threshold, total_bullets=total)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = os.path.join(output_dir, f"duplicate_bullet_report_{timestamp}.txt")
    os.makedirs(output_dir, exist_ok=True)

    if os.path.exists(output_path):
        answer = input(f"  Output file exists: {output_path}\n  Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("  Aborted.")
            return

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n  Written: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find duplicate bullets in experience_library.json"
    )
    parser.add_argument(
        "--threshold", type=float, default=85.0,
        help="Minimum similarity score to flag as duplicate (default: 85)"
    )
    parser.add_argument(
        "--library", default=LIBRARY_PATH,
        help=f"Path to experience_library.json (default: {LIBRARY_PATH})"
    )
    args = parser.parse_args()

    main(
        library_path=args.library,
        output_dir=OUTPUT_DIR,
        threshold=args.threshold,
    )
