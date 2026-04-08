# tests/phase3/test_parse_employer.py

import json
import pytest
import tempfile
from pathlib import Path
from scripts.utils.library_parser import (
    parse_library, save_employers, employer_to_filename
)

FIXTURE_MD = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.md"


def test_target_employer_written_to_file():
    employers, _ = parse_library(str(FIXTURE_MD))
    target_name = "Acme Defense Systems"
    assert target_name in employers

    with tempfile.TemporaryDirectory() as tmpdir:
        target_data = {target_name: employers[target_name]}
        save_employers(target_data, tmpdir)
        filename = employer_to_filename(target_name)
        path = Path(tmpdir) / filename
        assert path.exists()


def test_other_employers_not_in_targeted_output():
    employers, _ = parse_library(str(FIXTURE_MD))
    target_name = "Acme Defense Systems"

    with tempfile.TemporaryDirectory() as tmpdir:
        target_data = {target_name: employers[target_name]}
        saved = save_employers(target_data, tmpdir)
        assert len(saved) == 1
        assert employer_to_filename(target_name) in saved


def test_unknown_employer_not_in_parse_result():
    employers, _ = parse_library(str(FIXTURE_MD))
    assert "Nonexistent Corp" not in employers
