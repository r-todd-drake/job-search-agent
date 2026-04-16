import pytest
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.interview_library_parser as ilp


# ── Helpers ──────────────────────────────────────────────────────────────────

def _write_library(tmp_path, data, monkeypatch):
    lib_path = tmp_path / "interview_library.json"
    lib_path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(ilp, "LIBRARY_PATH", str(lib_path))
    return lib_path


def _sample_library():
    return {
        "stories": [
            {
                "id": "g2ops-mbse-bottleneck",
                "title": "MBSE bottleneck resolution",
                "tags": ["mbse", "systems-engineering"],
                "employer": "G2 OPS",
                "title_held": "Systems Engineer",
                "dates": "2021-2023",
                "situation": "Situation text.",
                "task": "Task text.",
                "action": "Action text.",
                "result": "Result text.",
                "if_probed": None,
                "notes": None,
                "source": "workshopped",
                "roles_used": ["Viasat_SE_IS"],
                "last_updated": "2026-04-15"
            },
            {
                "id": "shield-ai-cross-domain",
                "title": "Cross-domain PDR",
                "tags": ["cross-functional", "technical-credibility"],
                "employer": "Shield AI",
                "title_held": "Systems Architect",
                "dates": "2023-2024",
                "situation": "Situation text.",
                "task": "Task text.",
                "action": "Action text.",
                "result": "Result text.",
                "if_probed": "Probe text.",
                "notes": None,
                "source": "workshopped",
                "roles_used": ["Viasat_SE_IS", "Leidos_SE"],
                "last_updated": "2026-04-15"
            }
        ],
        "gap_responses": [
            {
                "id": "ip-networking-expertise",
                "gap_label": "IP Networking Expertise",
                "severity": "required",
                "tags": ["domain-gap"],
                "honest_answer": "Honest answer text.",
                "bridge": "Bridge text.",
                "redirect": "Redirect text.",
                "notes": None,
                "source": "workshopped",
                "roles_used": ["Viasat_SE_IS"],
                "last_updated": "2026-04-15"
            }
        ],
        "questions": [
            {
                "id": "what-does-success-look-like",
                "stage": "hiring_manager",
                "category": "success-metrics",
                "text": "What does success look like at 6 months?",
                "tags": ["program-delivery"],
                "notes": None,
                "source": "workshopped",
                "roles_used": ["Viasat_SE_IS"],
                "last_updated": "2026-04-15"
            },
            {
                "id": "where-are-integration-problems",
                "stage": "team_panel",
                "category": "integration-challenge",
                "text": "Where are the hard interface problems concentrated right now?",
                "tags": ["integration", "technical-credibility"],
                "notes": None,
                "source": "workshopped",
                "roles_used": ["Viasat_SE_IS"],
                "last_updated": "2026-04-15"
            }
        ]
    }


# ── init_library ──────────────────────────────────────────────────────────────

def test_init_library_creates_file_when_absent(tmp_path, monkeypatch):
    lib_path = tmp_path / "interview_library.json"
    monkeypatch.setattr(ilp, "LIBRARY_PATH", str(lib_path))
    assert not lib_path.exists()
    ilp.init_library()
    assert lib_path.exists()
    data = json.loads(lib_path.read_text())
    assert data == {"stories": [], "gap_responses": [], "questions": []}


def test_init_library_does_not_overwrite_existing(tmp_path, monkeypatch):
    existing = {"stories": [{"id": "keep-me"}], "gap_responses": [], "questions": []}
    lib_path = _write_library(tmp_path, existing, monkeypatch)
    ilp.init_library()
    data = json.loads(lib_path.read_text())
    assert data["stories"][0]["id"] == "keep-me"


# ── _load_library ─────────────────────────────────────────────────────────────

def test_load_library_returns_empty_when_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(ilp, "LIBRARY_PATH", str(tmp_path / "missing.json"))
    result = ilp._load_library()
    assert result == {"stories": [], "gap_responses": [], "questions": []}


def test_load_library_returns_content_when_present(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    result = ilp._load_library()
    assert len(result["stories"]) == 2
    assert len(result["gap_responses"]) == 1
    assert len(result["questions"]) == 2


# ── load_tags ─────────────────────────────────────────────────────────────────

def test_load_tags_returns_list(tmp_path, monkeypatch):
    tags_path = tmp_path / "tags.json"
    tags_path.write_text(json.dumps({"tags": ["mbse", "leadership"]}), encoding="utf-8")
    monkeypatch.setattr(ilp, "TAGS_PATH", str(tags_path))
    tags = ilp.load_tags()
    assert "mbse" in tags
    assert "leadership" in tags


def test_load_tags_returns_empty_when_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(ilp, "TAGS_PATH", str(tmp_path / "missing.json"))
    assert ilp.load_tags() == []


# ── get_stories ───────────────────────────────────────────────────────────────

def test_get_stories_returns_all_when_no_filters(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    result = ilp.get_stories()
    assert len(result) == 2


def test_get_stories_filters_by_tag(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    result = ilp.get_stories(tags=["mbse"])
    assert len(result) == 1
    assert result[0]["id"] == "g2ops-mbse-bottleneck"


def test_get_stories_tag_filter_is_or_within_tags(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    # Both stories match when tags list covers both
    result = ilp.get_stories(tags=["mbse", "cross-functional"])
    assert len(result) == 2


def test_get_stories_filters_by_role(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    result = ilp.get_stories(role="Leidos_SE")
    assert len(result) == 1
    assert result[0]["id"] == "shield-ai-cross-domain"


def test_get_stories_filters_by_tag_and_role(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    # shield-ai story has cross-functional tag and Leidos_SE role
    result = ilp.get_stories(tags=["cross-functional"], role="Leidos_SE")
    assert len(result) == 1
    assert result[0]["id"] == "shield-ai-cross-domain"


def test_get_stories_tag_and_role_no_match(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    # mbse tag exists, but not for Leidos_SE
    result = ilp.get_stories(tags=["mbse"], role="Leidos_SE")
    assert result == []


def test_get_stories_stage_param_accepted_without_error(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    # stage is accepted but not applied -- stories have no stage field
    result = ilp.get_stories(stage="hiring_manager")
    assert len(result) == 2  # all stories returned; stage filter is no-op


def test_get_stories_returns_empty_when_library_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(ilp, "LIBRARY_PATH", str(tmp_path / "missing.json"))
    assert ilp.get_stories(tags=["mbse"]) == []
