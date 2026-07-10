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
