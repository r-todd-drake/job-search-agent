# tests/phase3/test_compile_library.py

import json
import pytest
import tempfile
from pathlib import Path

FIXTURE_JSON = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.json"


def test_compile_library_includes_all_employers():
    from scripts.phase3_compile_library import compile_library

    fixture_data = json.loads(FIXTURE_JSON.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmpdir:
        employers_dir = Path(tmpdir) / "employers"
        employers_dir.mkdir()
        summaries_path = Path(tmpdir) / "summaries.json"

        for emp in fixture_data["employers"]:
            filename = emp["name"].lower().replace(" ", "_")[:40] + ".json"
            (employers_dir / filename).write_text(
                json.dumps(emp, indent=2), encoding="utf-8"
            )

        summaries_path.write_text(
            json.dumps({"total": 0, "summaries": []}, indent=2), encoding="utf-8"
        )

        chrono_order = [e["name"] for e in fixture_data["employers"]]
        library = compile_library(str(employers_dir), str(summaries_path),
                                  chrono_order=chrono_order)

    assert "employers" in library
    assert len(library["employers"]) == len(fixture_data["employers"])


def test_compile_library_has_metadata():
    from scripts.phase3_compile_library import compile_library

    fixture_data = json.loads(FIXTURE_JSON.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmpdir:
        employers_dir = Path(tmpdir) / "employers"
        employers_dir.mkdir()
        summaries_path = Path(tmpdir) / "summaries.json"

        for emp in fixture_data["employers"]:
            filename = emp["name"].lower().replace(" ", "_")[:40] + ".json"
            (employers_dir / filename).write_text(json.dumps(emp), encoding="utf-8")
        summaries_path.write_text(
            json.dumps({"total": 0, "summaries": []}), encoding="utf-8"
        )

        chrono_order = [e["name"] for e in fixture_data["employers"]]
        library = compile_library(str(employers_dir), str(summaries_path),
                                  chrono_order=chrono_order)

    assert "metadata" in library
    assert "total_employers" in library["metadata"]


def test_no_module_level_execution_on_import():
    import scripts.phase3_compile_library  # noqa: F401
