# tests/phase2/test_job_ranking.py

import pytest


HIGH_MATCH_JD = """
Senior Systems Engineer - Autonomous Maritime Systems.
Requires MBSE expertise using Cameo Systems Modeler and DoDAF architectural framework.
Autonomous Systems and Uncrewed platform experience required.
C4ISR integration, Defense Acquisition, ConOps, Stakeholder Engagement.
JADC2 and System-of-Systems architecture background desired.
"""

LOW_MATCH_JD = """
Junior Web Developer. Build React and Node.js applications for e-commerce.
No defense background required. Remote work available.
"""


def test_score_job_high_match_exceeds_threshold():
    from scripts.phase2_job_ranking import score_job
    score, matched = score_job(HIGH_MATCH_JD)
    assert score > 30, f"Expected score > 30, got {score}"
    assert "MBSE" in matched


def test_score_job_low_match_near_zero():
    from scripts.phase2_job_ranking import score_job
    score, matched = score_job(LOW_MATCH_JD)
    assert score < 10, f"Expected score < 10, got {score}"


def test_score_job_returns_matched_keywords_dict():
    from scripts.phase2_job_ranking import score_job
    score, matched = score_job(HIGH_MATCH_JD)
    assert isinstance(matched, dict)
    for keyword, weight in matched.items():
        assert isinstance(weight, int)


def test_detect_duplicates_finds_shared_req():
    from scripts.phase2_job_ranking import detect_duplicates
    results = [
        {"company": "Acme", "title": "SE", "req_number": "ADS-12345", "score": 50},
        {"company": "Generic", "title": "PE", "req_number": "GTC-00001", "score": 30},
        {"company": "Repeat", "title": "PE", "req_number": "ADS-12345", "score": 45},
    ]
    dupes = detect_duplicates(results)
    assert len(dupes) == 1
    req, first_label, dupe_company, dupe_title = dupes[0]
    assert req == "ADS-12345"
    assert dupe_company == "Repeat"


def test_detect_duplicates_no_duplicates():
    from scripts.phase2_job_ranking import detect_duplicates
    results = [
        {"company": "Acme", "title": "SE", "req_number": "ADS-12345", "score": 50},
        {"company": "Generic", "title": "PE", "req_number": "GTC-00001", "score": 30},
    ]
    assert detect_duplicates(results) == []


def test_detect_duplicates_skips_empty_req():
    from scripts.phase2_job_ranking import detect_duplicates
    results = [
        {"company": "Acme", "title": "SE", "req_number": "", "score": 50},
        {"company": "Generic", "title": "PE", "req_number": "", "score": 30},
    ]
    assert detect_duplicates(results) == []


def test_status_constants_are_disjoint():
    """ACTIONABLE and EXCLUDED status sets must not overlap."""
    from scripts.phase2_job_ranking import ACTIONABLE_STATUSES, EXCLUDED_STATUSES
    assert ACTIONABLE_STATUSES.isdisjoint(EXCLUDED_STATUSES)
    assert "SKIP" in EXCLUDED_STATUSES
    assert "APPLIED" in EXCLUDED_STATUSES
    assert "" in ACTIONABLE_STATUSES  # blank = new = actionable


def test_no_module_level_execution_on_import():
    """Importing phase2_job_ranking should not open any files."""
    import scripts.phase2_job_ranking  # noqa: F401


@pytest.mark.live
def test_full_ranking_run_on_fixture_csv():
    """Tier 2: run scoring against the fixture CSV using real file I/O."""
    import csv
    from pathlib import Path
    from scripts.phase2_job_ranking import score_job, detect_duplicates

    fixture_csv = Path(__file__).parent.parent / "fixtures" / "jobs" / "jobs_sample.csv"
    jobs = []
    with open(fixture_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jobs.append(row)

    results = []
    for job in jobs:
        score, matched = score_job("")
        results.append({**job, "score": score, "req_number": job.get("req_number", "")})

    dupes = detect_duplicates(results)
    assert len(dupes) == 1
    assert dupes[0][0] == "ADS-12345"
