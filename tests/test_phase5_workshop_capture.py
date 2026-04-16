import pytest
import json
import os
import sys
from unittest.mock import MagicMock, patch
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.phase5_workshop_capture as wc


# ── Helpers ───────────────────────────────────────────────────────────────────

def _seed_library(tmp_path, data, monkeypatch):
    """Write library data to a temp file and monkeypatch LIBRARY_PATH."""
    import scripts.interview_library_parser as ilp
    lib_path = tmp_path / "interview_library.json"
    lib_path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(ilp, "LIBRARY_PATH", str(lib_path))
    return lib_path


# ── Argparse ──────────────────────────────────────────────────────────────────

def test_argparse_requires_role():
    with pytest.raises(SystemExit):
        wc.build_parser().parse_args(["--stage", "hiring_manager"])


def test_argparse_requires_stage():
    with pytest.raises(SystemExit):
        wc.build_parser().parse_args(["--role", "TestRole"])


def test_argparse_valid_args():
    args = wc.build_parser().parse_args(["--role", "TestRole", "--stage", "hiring_manager"])
    assert args.role == "TestRole"
    assert args.stage == "hiring_manager"


# ── Docx location ─────────────────────────────────────────────────────────────

def test_locate_docx_exits_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(wc, "JOBS_PACKAGES_DIR", str(tmp_path))
    with pytest.raises(SystemExit):
        wc._locate_docx("TestRole", "hiring_manager")


def test_locate_docx_returns_path_when_present(tmp_path, monkeypatch):
    pkg = tmp_path / "TestRole"
    pkg.mkdir()
    docx_path = pkg / "interview_prep_hiring_manager.docx"
    docx_path.write_bytes(b"")
    monkeypatch.setattr(wc, "JOBS_PACKAGES_DIR", str(tmp_path))
    result = wc._locate_docx("TestRole", "hiring_manager")
    assert result == str(docx_path)
