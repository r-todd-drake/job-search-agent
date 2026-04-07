# tests/phase3/test_parse_library.py

import json
import pytest
import tempfile
from pathlib import Path
from scripts.utils.library_parser import parse_library, save_employers, save_summaries

FIXTURE_MD = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.md"


def test_parse_and_save_creates_employer_json_files():
    employers, summaries = parse_library(str(FIXTURE_MD))
    with tempfile.TemporaryDirectory() as tmpdir:
        saved = save_employers(employers, tmpdir)
        assert len(saved) >= 1
        for filename in saved:
            path = Path(tmpdir) / filename
            assert path.exists()
            data = json.loads(path.read_text(encoding="utf-8"))
            assert "name" in data
            assert "bullets" in data


def test_parse_and_save_output_is_valid_json():
    employers, summaries = parse_library(str(FIXTURE_MD))
    with tempfile.TemporaryDirectory() as tmpdir:
        saved = save_employers(employers, tmpdir)
        for filename in saved:
            path = Path(tmpdir) / filename
            json.loads(path.read_text(encoding="utf-8"))  # Should not raise


def test_save_summaries_creates_file():
    _, summaries = parse_library(str(FIXTURE_MD))
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = str(Path(tmpdir) / "summaries.json")
        save_summaries(summaries, output_path)
        assert Path(output_path).exists()
        data = json.loads(Path(output_path).read_text(encoding="utf-8"))
        assert "summaries" in data
        assert "total" in data
