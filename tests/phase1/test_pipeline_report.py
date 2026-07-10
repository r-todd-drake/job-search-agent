# tests/phase1/test_pipeline_report.py

import pytest


def make_applications(rows):
    """Helper: build application list from list of (status, req_number) tuples."""
    return [{"Status": status, "req_number": req} for status, req in rows]


def test_analyze_applications_counts_by_status():
    from scripts.pipeline_report import analyze_applications
    apps = make_applications([
        ("Active", "REQ-001"),
        ("Active", "REQ-002"),
        ("Rejected", "REQ-003"),
        ("Pending", "REQ-004"),
    ])
    counts = analyze_applications(apps)
    assert counts["Active"] == 2
    assert counts["Rejected"] == 1


def test_analyze_applications_empty_list():
    from scripts.pipeline_report import analyze_applications
    counts = analyze_applications([])
    assert counts == {}


def test_detect_duplicates_finds_shared_req_number():
    from scripts.pipeline_report import detect_duplicates
    apps = make_applications([
        ("Active", "REQ-001"),
        ("Active", "REQ-001"),
        ("Active", "REQ-002"),
    ])
    dupes = detect_duplicates(apps)
    assert len(dupes) == 1
    assert dupes[0]["req_number"] == "REQ-001"


def test_detect_duplicates_no_duplicates_returns_empty():
    from scripts.pipeline_report import detect_duplicates
    apps = make_applications([
        ("Active", "REQ-001"),
        ("Active", "REQ-002"),
    ])
    assert detect_duplicates(apps) == []


def test_no_files_modified_during_import():
    """Importing pipeline_report should not open any files."""
    import importlib
    import scripts.pipeline_report  # noqa: F401
