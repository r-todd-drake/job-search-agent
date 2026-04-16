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
