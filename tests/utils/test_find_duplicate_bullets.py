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
