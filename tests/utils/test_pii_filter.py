# tests/utils/test_pii_filter.py

import os
import pytest


def test_strip_pii_replaces_name(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "")
    monkeypatch.setenv("CANDIDATE_EMAIL", "")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "")
    monkeypatch.setenv("CANDIDATE_GITHUB", "")

    import importlib
    import scripts.utils.pii_filter as pii_module
    importlib.reload(pii_module)

    result = pii_module.strip_pii("Contact Jane Q. Applicant for details.")
    assert "Jane Q. Applicant" not in result
    assert "[CANDIDATE]" in result


def test_strip_pii_replaces_all_five_types(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "(555) 867-5309")
    monkeypatch.setenv("CANDIDATE_EMAIL", "applicant@example.com")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "linkedin.com/in/applicant")
    monkeypatch.setenv("CANDIDATE_GITHUB", "github.com/applicant")

    import importlib
    import scripts.utils.pii_filter as pii_module
    importlib.reload(pii_module)

    text = (
        "Name: Jane Q. Applicant | Phone: (555) 867-5309 | "
        "Email: applicant@example.com | "
        "linkedin.com/in/applicant | github.com/applicant"
    )
    result = pii_module.strip_pii(text)

    assert "Jane Q. Applicant" not in result
    assert "(555) 867-5309" not in result
    assert "applicant@example.com" not in result
    assert "linkedin.com/in/applicant" not in result
    assert "github.com/applicant" not in result


def test_strip_pii_mid_sentence(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "")
    monkeypatch.setenv("CANDIDATE_EMAIL", "")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "")
    monkeypatch.setenv("CANDIDATE_GITHUB", "")

    import importlib
    import scripts.utils.pii_filter as pii_module
    importlib.reload(pii_module)

    result = pii_module.strip_pii("Please reach Jane Q. Applicant at your earliest convenience.")
    assert "Jane Q. Applicant" not in result


def test_strip_pii_no_pii_in_text_returns_unchanged(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "(555) 867-5309")
    monkeypatch.setenv("CANDIDATE_EMAIL", "applicant@example.com")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "linkedin.com/in/applicant")
    monkeypatch.setenv("CANDIDATE_GITHUB", "github.com/applicant")

    import importlib
    import scripts.utils.pii_filter as pii_module
    importlib.reload(pii_module)

    original = "Senior systems engineer with MBSE expertise."
    result = pii_module.strip_pii(original)
    assert result == original


def test_strip_pii_empty_string_returns_unchanged(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "(555) 867-5309")
    monkeypatch.setenv("CANDIDATE_EMAIL", "applicant@example.com")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "linkedin.com/in/applicant")
    monkeypatch.setenv("CANDIDATE_GITHUB", "github.com/applicant")

    import importlib
    import scripts.utils.pii_filter as pii_module
    importlib.reload(pii_module)

    assert pii_module.strip_pii("") == ""
    assert pii_module.strip_pii(None) is None
