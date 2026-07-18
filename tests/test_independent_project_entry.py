# tests/test_independent_project_entry.py
#
# Consistency checks for the gap-closing INDEPENDENT PROJECT entry, which was
# added by hand to experience_library.json and candidate_config.yaml.
# Verifies: presence in both files, byte-identical names, tier 1 at position 0,
# and schema parity with the compiled employer entries.
#
# Skipped automatically when the personal (gitignored) data files are absent.

import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
LIBRARY_JSON = ROOT / "data" / "experience_library" / "experience_library.json"
CONFIG_YAML = ROOT / "context" / "candidate" / "candidate_config.yaml"

ENTRY_NAME = "INDEPENDENT PROJECT"

pytestmark = pytest.mark.skipif(
    not (LIBRARY_JSON.exists() and CONFIG_YAML.exists()),
    reason="personal data files not present (gitignored)",
)


@pytest.fixture(scope="module")
def library():
    with open(LIBRARY_JSON, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def config():
    with open(CONFIG_YAML, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_entry_is_first_employer_in_library(library):
    assert library["employers"][0]["name"] == ENTRY_NAME


def test_entry_is_first_employer_in_config_with_tier_1(config):
    first = config["employers"][0]
    assert first["name"] == ENTRY_NAME
    assert first["tier"] == 1


def test_names_match_exactly_between_config_and_library(library, config):
    lib_name = library["employers"][0]["name"]
    cfg_name = config["employers"][0]["name"]
    assert lib_name == cfg_name
    assert lib_name.encode("utf-8") == cfg_name.encode("utf-8")


def test_entry_schema_parity_with_other_employers(library):
    employers = library["employers"]
    entry = employers[0]
    for other in employers[1:]:
        assert set(entry.keys()) == set(other.keys()), (
            f"employer-level key mismatch vs {other['name']}"
        )
    entry_bullet = entry["bullets"][0]
    for other in employers[1:]:
        other_bullet = other["bullets"][0]
        assert set(entry_bullet.keys()) == set(other_bullet.keys()), (
            f"bullet key mismatch vs {other['name']}"
        )
        for key in entry_bullet:
            assert type(entry_bullet[key]) is type(other_bullet[key]), (
                f"bullet field '{key}' type mismatch vs {other['name']}: "
                f"{type(entry_bullet[key]).__name__} != {type(other_bullet[key]).__name__}"
            )


def test_entry_dates_use_en_dash(library):
    dates = library["employers"][0]["dates"]
    assert "–" in dates, "dates must use an en dash (U+2013)"
    assert "—" not in dates, "dates must not contain an em dash"
    assert " - " not in dates, "dates must not use a plain hyphen separator"


def test_entry_has_no_em_dash_anywhere(library):
    entry_text = json.dumps(library["employers"][0], ensure_ascii=False)
    assert "—" not in entry_text


def test_metadata_reflects_entry(library):
    meta = library["metadata"]
    employers = library["employers"]
    assert meta["total_employers"] == len(employers)
    assert meta["employer_names"][0] == ENTRY_NAME
    assert meta["employer_names"] == [e["name"] for e in employers]
    assert meta["total_bullets"] == sum(len(e["bullets"]) for e in employers)


def test_entry_config_fields_match_other_config_employers(config):
    employers = config["employers"]
    entry_keys = set(employers[0].keys())
    for other in employers[1:]:
        assert entry_keys == set(other.keys()), (
            f"config employer key mismatch vs {other['name']}"
        )
