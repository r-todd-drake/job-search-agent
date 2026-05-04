# Find Duplicate Bullets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `scripts/utils/find_duplicate_bullets.py` — a standalone utility that scans `experience_library.json` for same or near-duplicate bullets across all employers using rapidfuzz, and writes a grouped cluster report to `outputs/`.

**Architecture:** A single pure function `find_duplicate_clusters(bullets, threshold)` handles all matching and clustering via union-find; two private helpers (`_compute_pairs`, `_build_clusters`) keep each stage testable in isolation. A separate `format_cluster_report()` function owns all output formatting. The CLI `main()` handles file I/O and wires these together — same pattern as `generate_message()` in `phase6_networking.py`.

**Tech Stack:** Python 3.11, rapidfuzz (already in requirements.txt), argparse, pytest

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `scripts/utils/find_duplicate_bullets.py` | All matching, clustering, formatting, and CLI |
| Create | `tests/utils/test_find_duplicate_bullets.py` | 13 Tier 1 mock tests |
| Modify | `context/SCRIPT_INDEX.md` | Add row under "One-time / utility scripts" |
| Modify | `context/DATA_FLOW.md` | Add row under "Shared modules" |

---

## Task 1: Test file skeleton — core matching tests (5 tests)

**Files:**
- Create: `tests/utils/test_find_duplicate_bullets.py`

- [ ] **Step 1: Write the failing test file**

```python
# tests/utils/test_find_duplicate_bullets.py

import pytest
from scripts.utils.find_duplicate_bullets import find_duplicate_clusters, format_cluster_report

# ---------------------------------------------------------------------------
# Fixtures — Jane Q. Applicant / Acme Defense Systems identity
# ---------------------------------------------------------------------------

B_ADS_001 = {
    "id": "ADS_001", "theme": "Leadership",
    "text": "Led cross-functional team of 12 engineers to deliver program on schedule",
    "employer": "Acme Defense Systems",
}
B_ADS_002 = {
    "id": "ADS_002", "theme": "Leadership",
    "text": "Led cross-functional team of 12 engineers to deliver program on time",
    "employer": "Acme Defense Systems",
}
B_ADS_003 = {
    "id": "ADS_003", "theme": "Results",
    "text": "Reduced deployment cycle time by 40% through process automation initiatives",
    "employer": "Acme Defense Systems",
}
B_GCI_001 = {
    "id": "GCI_001", "theme": "Leadership",
    "text": "Led cross-functional team of 12 engineers to deliver program on schedule",
    "employer": "General Components Inc",
}
B_GCI_002 = {
    "id": "GCI_002", "theme": "Technical",
    "text": "Architected microservices platform serving two million daily active users",
    "employer": "General Components Inc",
}
B_GCI_003 = {
    "id": "GCI_003", "theme": "Results",
    "text": "Decreased deployment cycle time by 40% via process automation initiatives",
    "employer": "General Components Inc",
}


# ---------------------------------------------------------------------------
# Task 1 tests: edge cases and basic matching
# ---------------------------------------------------------------------------

def test_empty_library_returns_no_clusters():
    assert find_duplicate_clusters([]) == []


def test_single_bullet_returns_no_clusters():
    assert find_duplicate_clusters([B_ADS_001]) == []


def test_identical_text_triggers_cluster():
    # B_ADS_001 and B_GCI_001 have identical text -- cross-employer duplicate
    clusters = find_duplicate_clusters([B_ADS_001, B_GCI_001, B_GCI_002])
    assert len(clusters) == 1
    ids = {b["id"] for b in clusters[0]["bullets"]}
    assert ids == {"ADS_001", "GCI_001"}


def test_identical_text_score_is_100():
    clusters = find_duplicate_clusters([B_ADS_001, B_GCI_001])
    assert clusters[0]["max_score"] == 100.0


def test_below_threshold_excluded():
    # B_GCI_002 is clearly different -- should not appear in any cluster at threshold=85
    clusters = find_duplicate_clusters([B_ADS_001, B_GCI_001, B_GCI_002])
    cluster_ids = {b["id"] for cluster in clusters for b in cluster["bullets"]}
    assert "GCI_002" not in cluster_ids
```

- [ ] **Step 2: Run tests to confirm they fail with ImportError**

```
pytest tests/utils/test_find_duplicate_bullets.py -v
```

Expected: 5 ERRORs — `ModuleNotFoundError: No module named 'scripts.utils.find_duplicate_bullets'`

---

## Task 2: Implement `find_duplicate_clusters()` and helpers

**Files:**
- Create: `scripts/utils/find_duplicate_bullets.py`

- [ ] **Step 1: Write the module with all matching and clustering logic**

```python
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
```

- [ ] **Step 2: Run Task 1 tests to verify they pass**

```
pytest tests/utils/test_find_duplicate_bullets.py -v -k "Task 1 or empty or single or identical or below_threshold"
```

Expected: 5 PASSED

- [ ] **Step 3: Run full mock suite to verify no regressions**

```
pytest tests/ -m "not live" -v
```

Expected: all previously passing tests still PASSED

- [ ] **Step 4: Commit**

```bash
git add tests/utils/test_find_duplicate_bullets.py scripts/utils/find_duplicate_bullets.py
git commit -m "feat(utils): add find_duplicate_clusters with union-find clustering and 5 passing tests"
```

---

## Task 3: Add remaining 8 tests — matching behavior and output formatting

**Files:**
- Modify: `tests/utils/test_find_duplicate_bullets.py`

- [ ] **Step 1: Append the remaining 8 tests to the test file**

Add these after the Task 1 tests (inside the same file):

```python
# ---------------------------------------------------------------------------
# Task 3 tests: matching behavior
# ---------------------------------------------------------------------------

def test_near_duplicate_above_threshold_included():
    # B_ADS_001 and B_ADS_002 differ only in final word; score ~93% at threshold=85
    clusters = find_duplicate_clusters([B_ADS_001, B_ADS_002], threshold=85.0)
    assert len(clusters) == 1


def test_cross_employer_matching():
    # B_ADS_003 and B_GCI_003 are from different employers but nearly identical
    clusters = find_duplicate_clusters([B_ADS_003, B_GCI_003], threshold=75.0)
    assert len(clusters) == 1
    employers = {b["employer"] for b in clusters[0]["bullets"]}
    assert "Acme Defense Systems" in employers
    assert "General Components Inc" in employers


def test_same_employer_matching():
    # B_ADS_001 and B_ADS_002 are both from Acme Defense Systems -- same-employer dupes caught
    clusters = find_duplicate_clusters([B_ADS_001, B_ADS_002], threshold=85.0)
    assert len(clusters) == 1
    employers = [b["employer"] for b in clusters[0]["bullets"]]
    assert all(e == "Acme Defense Systems" for e in employers)


def test_cluster_grouping_transitive():
    # B_ADS_001 ~ B_GCI_001 (identical), B_ADS_001 ~ B_ADS_002 (near-dup)
    # All three must land in one cluster via union-find transitivity
    clusters = find_duplicate_clusters(
        [B_ADS_001, B_ADS_002, B_GCI_001], threshold=85.0
    )
    assert len(clusters) == 1
    assert len(clusters[0]["bullets"]) == 3


def test_unique_bullets_produce_no_clusters():
    # B_ADS_001 (leadership) and B_GCI_002 (technical) are unrelated
    clusters = find_duplicate_clusters([B_ADS_001, B_GCI_002], threshold=85.0)
    assert clusters == []


# ---------------------------------------------------------------------------
# Task 3 tests: output formatting
# ---------------------------------------------------------------------------

def test_output_contains_bullet_ids():
    clusters = find_duplicate_clusters([B_ADS_001, B_GCI_001])
    report = format_cluster_report(clusters, threshold=85.0, total_bullets=2)
    assert "ADS_001" in report
    assert "GCI_001" in report


def test_output_contains_employer_names():
    clusters = find_duplicate_clusters([B_ADS_001, B_GCI_001])
    report = format_cluster_report(clusters, threshold=85.0, total_bullets=2)
    assert "Acme Defense Systems" in report
    assert "General Components Inc" in report


def test_output_contains_theme_labels():
    clusters = find_duplicate_clusters([B_ADS_001, B_GCI_001])
    report = format_cluster_report(clusters, threshold=85.0, total_bullets=2)
    assert "Leadership" in report


def test_empty_clusters_report_message():
    report = format_cluster_report([], threshold=85.0, total_bullets=5)
    assert "No duplicate clusters found" in report
```

- [ ] **Step 2: Run tests to confirm the 4 formatting tests fail with NameError**

```
pytest tests/utils/test_find_duplicate_bullets.py -v
```

Expected: 9 PASSED (matching tests), 4 FAILED with `ImportError` or `AttributeError` on `format_cluster_report`

---

## Task 4: Implement `format_cluster_report()`

**Files:**
- Modify: `scripts/utils/find_duplicate_bullets.py`

- [ ] **Step 1: Add `format_cluster_report()` to the module, before the `main()` placeholder**

Insert this function after `find_duplicate_clusters()` in the file:

```python
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
```

- [ ] **Step 2: Run all 13 tests to verify they all pass**

```
pytest tests/utils/test_find_duplicate_bullets.py -v
```

Expected: 13 PASSED

- [ ] **Step 3: Run full mock suite to verify no regressions**

```
pytest tests/ -m "not live" -v
```

Expected: all previously passing tests still PASSED

- [ ] **Step 4: Commit**

```bash
git add tests/utils/test_find_duplicate_bullets.py scripts/utils/find_duplicate_bullets.py
git commit -m "feat(utils): add format_cluster_report; all 13 duplicate-bullet tests passing"
```

---

## Task 5: Wire up CLI — `_extract_bullets()`, `main()`, argparse

**Files:**
- Modify: `scripts/utils/find_duplicate_bullets.py`

- [ ] **Step 1: Add `main()` and the `__main__` block to the module**

Append to the end of `scripts/utils/find_duplicate_bullets.py`:

```python
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
```

- [ ] **Step 2: Run all 13 tests again to confirm nothing broke**

```
pytest tests/utils/test_find_duplicate_bullets.py -v
```

Expected: 13 PASSED

- [ ] **Step 3: Run a syntax check**

```
python -m py_compile scripts/utils/find_duplicate_bullets.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 4: Smoke-test the CLI against the fixture library**

```
python -m scripts.utils.find_duplicate_bullets --library tests/fixtures/library/experience_library.json --threshold 85
```

Expected: script runs, prints bullet count and cluster count, writes a report to `outputs/`. No exceptions.

- [ ] **Step 5: Commit**

```bash
git add scripts/utils/find_duplicate_bullets.py
git commit -m "feat(utils): wire up find_duplicate_bullets CLI with argparse and file I/O"
```

---

## Task 6: Update context indexes

**Files:**
- Modify: `context/SCRIPT_INDEX.md`
- Modify: `context/DATA_FLOW.md`

- [ ] **Step 1: Add row to SCRIPT_INDEX.md under "One-time / utility scripts"**

In `context/SCRIPT_INDEX.md`, find the table under **One-time / utility scripts** and add this row. The existing table has 2 columns (Script | Purpose) — keep it 2 columns and embed the flags in the Purpose cell:

```
| `utils/find_duplicate_bullets.py` | Scan experience_library.json for same or near-duplicate bullets across all employers; writes grouped cluster report to outputs/. Flags: `--threshold` (default 85) `--library` |
```

The table after the edit should look like:

```markdown
## One-time / utility scripts

| Script                 | Purpose                                                                                                |
| ---------------------- | ------------------------------------------------------------------------------------------------------ |
| `utils/build_docs.py`  | Assemble README.md and PROJECT_CONTEXT.md from templates + fragments. Run after editing any fragment or template. `python scripts/utils/build_docs.py` or `--doc [filename]` |
| `utils/find_duplicate_bullets.py` | Scan experience_library.json for same or near-duplicate bullets across all employers; writes grouped cluster report to outputs/. Flags: `--threshold` (default 85) `--library` |
| `utils/normalize_library.py` | Merge tranche-suffixed employer sections in experience_library.md                                 |
| `utils/diagnose_*.py`  | Development diagnostics -- not part of the production workflow                                        |
```

- [ ] **Step 2: Add row to DATA_FLOW.md under "Shared modules"**

In `context/DATA_FLOW.md`, find the **Shared modules** table at the bottom and add this row. The existing table has 2 columns (Module | Reads / writes on behalf of callers) — keep it 2 columns and combine reads/writes into one cell:

```
| `utils/find_duplicate_bullets.py` | Reads `data/experience_library/experience_library.json`; writes `outputs/duplicate_bullet_report_YYYYMMDD_HHMM.txt` |
```

The table after the edit should look like:

```markdown
## Shared modules

| Module | Reads / writes on behalf of callers |
| ------ | ------------------------------------ |
| `utils/library_parser.py` | Reads `data/experience_library/experience_library.md` |
| `utils/pii_filter.py` | Reads `.env` (PII values to strip before API calls -- not a data file) |
| `utils/find_duplicate_bullets.py` | Reads `data/experience_library/experience_library.json`; writes `outputs/duplicate_bullet_report_YYYYMMDD_HHMM.txt` |
| `interview_library_parser.py` | Reads and writes `data/interview_library.json`; reads `data/interview_library_tags.json` |
| `phase5_debrief_utils.py` | Reads `data/debriefs/[role]/*.json` (all filed debriefs for a role) |
```

- [ ] **Step 3: Run full mock suite one final time**

```
pytest tests/ -m "not live" -v
```

Expected: all tests PASSED

- [ ] **Step 4: Final commit**

```bash
git add context/SCRIPT_INDEX.md context/DATA_FLOW.md
git commit -m "docs: add find_duplicate_bullets to SCRIPT_INDEX and DATA_FLOW"
```

---

## Files Created or Modified

| Action | Path |
|--------|------|
| **Create** | `scripts/utils/find_duplicate_bullets.py` |
| **Create** | `tests/utils/test_find_duplicate_bullets.py` |
| **Modify** | `context/SCRIPT_INDEX.md` |
| **Modify** | `context/DATA_FLOW.md` |

No other files are touched. `experience_library.json` and all data files remain read-only.

---

## Architecture Notes

**Why union-find for clustering?**
Simple greedy "first match wins" grouping can split a cluster when A matches B and B matches C but A does not directly match C. Union-find handles transitivity correctly: any two bullets connected through any chain of matches end up in one cluster regardless of whether they match each other directly. This is the right choice for a deduplication tool where the user wants to see the full equivalence class.

**Why `token_sort_ratio` and not `ratio` or `partial_ratio`?**
This is the same scorer used in `phase4_backport.py`. `token_sort_ratio` sorts both strings' tokens before comparing, which makes it insensitive to word-order variations ("Led team of 12" vs "team of 12 Led"). This matches the backport script's established convention and avoids introducing a second scoring convention into the project.

**`format_cluster_report()` uses en dashes (`--`) in pairwise score lines** per the project-wide en-dash convention (DECISIONS_LOG.md). The `--` separator between IDs is intentional: it is a CLI-style pair separator, not a typographic dash.
