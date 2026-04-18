# Workshop Capture and Interview Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the interview library infrastructure (a queryable JSON store and parser module) and the workshop capture script that parses a workshopped interview prep .docx and writes durable, role-portable content into the library.

**Architecture:** Two independent subsystems built in sequence. Session A produces `interview_library_parser.py` -- a clean module that owns all library read/init operations and is importable by future scripts with no side effects. Session B produces `phase5_workshop_capture.py` -- a CLI script that parses a workshopped .docx into structured entries, confirms with the user, handles duplicates, and writes to the library. The capture script imports from the parser module; all library writes go through the parser's data structures.

**Tech Stack:** Python 3, python-docx (already a project dependency), pytest, json, re, argparse, datetime

---

## Files Created or Modified

**Session A -- Library Infrastructure:**
- Create: `data/interview_library_tags.json` -- controlled tag vocabulary (20 tags)
- Create: `data/interview_library.json` -- initialized empty by `init_library()` on first run
- Create: `scripts/interview_library_parser.py` -- owns LIBRARY_PATH, TAGS_PATH, init_library, load_tags, get_stories, get_gap_responses, get_questions
- Create: `tests/test_interview_library_parser.py` -- parser unit tests (no file I/O; uses monkeypatch + tmp_path)

**Session B -- Workshop Capture Script:**
- Create: `scripts/phase5_workshop_capture.py` -- CLI capture script; imports from interview_library_parser
- Create: `tests/test_phase5_workshop_capture.py` -- capture unit tests (docx extraction mocked; library writes use tmp_path)

---

## Context for the Executing CC Instance

**Read before starting -- in this order:**
1. `CLAUDE.md` -- safety rules, code style (en dashes, no PII)
2. `docs/features/phase5-workshop-capture/proposal.md` -- primary spec; all acceptance criteria
3. `docs/superpowers/plans/2026-04-15-workshop-capture.md` -- this plan
4. `tests/test_phase5_thankyou.py` -- test pattern reference (monkeypatch, tmp_path, MagicMock style used in this project)

**For Session B only -- also read:**
5. `scripts/phase5_interview_prep.py` -- understand `generate_prep_docx` and `parse_and_add_section` to know exactly what paragraph structure the workshopped .docx contains

**Do NOT read** (large files not relevant to this session):
- `scripts/phase5_debrief.py`
- `scripts/phase4_resume_generator.py`

---

## ═══════════════════════════════════════════
## SESSION A: Library Infrastructure
## ═══════════════════════════════════════════

---

### Task 1: Create data files

**Files:**
- Create: `data/interview_library_tags.json`
- Create: `data/interview_library.json`

- [ ] **Step 1.1: Write interview_library_tags.json**

```json
{
  "tags": [
    "leadership",
    "cross-functional",
    "technical-credibility",
    "ambiguity",
    "stakeholder-management",
    "program-delivery",
    "systems-engineering",
    "communication",
    "conflict-resolution",
    "domain-gap",
    "tools-gap",
    "clearance",
    "salary",
    "culture-fit",
    "mbse",
    "requirements-analysis",
    "integration",
    "v-and-v",
    "architecture",
    "domain-translation"
  ]
}
```

Save to `data/interview_library_tags.json`.

- [ ] **Step 1.2: Write the empty library file**

```json
{
  "stories": [],
  "gap_responses": [],
  "questions": []
}
```

Save to `data/interview_library.json`.

- [ ] **Step 1.3: Verify both files are valid JSON**

```bash
python -c "import json; json.load(open('data/interview_library_tags.json'))" && echo OK
python -c "import json; json.load(open('data/interview_library.json'))" && echo OK
```

Expected: `OK` twice.

- [ ] **Step 1.4: Commit**

```bash
git add data/interview_library_tags.json data/interview_library.json
git commit -m "Add interview library data files (empty library, tag vocabulary)"
```

---

### Task 2: Parser module scaffold -- init and load

**Files:**
- Create: `scripts/interview_library_parser.py`
- Create: `tests/test_interview_library_parser.py`

- [ ] **Step 2.1: Write failing tests for init_library and _load_library**

Create `tests/test_interview_library_parser.py`:

```python
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
```

- [ ] **Step 2.2: Run tests -- confirm they fail**

```bash
python -m pytest tests/test_interview_library_parser.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError` or `AttributeError` -- the module does not exist yet.

- [ ] **Step 2.3: Write scripts/interview_library_parser.py -- scaffold + init + load + load_tags**

```python
# ==============================================
# interview_library_parser.py
# Owns all read/init operations on the interview
# library. Importable by any Phase 5 script
# with no side effects.
#
# Usage (from other scripts):
#   from scripts.interview_library_parser import (
#       get_stories, get_gap_responses, get_questions,
#       init_library, load_tags
#   )
# ==============================================

import json
import os

LIBRARY_PATH = "data/interview_library.json"
TAGS_PATH = "data/interview_library_tags.json"

_EMPTY_LIBRARY = {"stories": [], "gap_responses": [], "questions": []}


def init_library():
    """Create empty library file if it does not exist. Never overwrites existing content."""
    if os.path.exists(LIBRARY_PATH):
        return
    os.makedirs(os.path.dirname(LIBRARY_PATH), exist_ok=True)
    with open(LIBRARY_PATH, "w", encoding="utf-8") as f:
        json.dump(dict(_EMPTY_LIBRARY), f, indent=2)


def _load_library():
    """Load library from disk. Returns empty structure if file absent."""
    if not os.path.exists(LIBRARY_PATH):
        return {k: list(v) for k, v in _EMPTY_LIBRARY.items()}
    with open(LIBRARY_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_tags():
    """Load controlled tag vocabulary. Returns empty list if file absent."""
    if not os.path.exists(TAGS_PATH):
        return []
    with open(TAGS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("tags", [])
```

*(get_stories, get_gap_responses, get_questions to be added in Task 3 and 4)*

- [ ] **Step 2.4: Run tests -- confirm they pass**

```bash
python -m pytest tests/test_interview_library_parser.py -v
```

Expected: 7 passed.

- [ ] **Step 2.5: Syntax check**

```bash
python -m py_compile scripts/interview_library_parser.py && echo OK
```

---

### Task 3: Implement get_stories and its tests

**Files:**
- Modify: `scripts/interview_library_parser.py`
- Modify: `tests/test_interview_library_parser.py`

- [ ] **Step 3.1: Append get_stories tests to the test file**

Add to `tests/test_interview_library_parser.py`:

```python
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
```

- [ ] **Step 3.2: Run tests -- confirm new tests fail**

```bash
python -m pytest tests/test_interview_library_parser.py::test_get_stories_returns_all_when_no_filters -v
```

Expected: `AttributeError: module has no attribute 'get_stories'`

- [ ] **Step 3.3: Append get_stories to scripts/interview_library_parser.py**

Add after `load_tags()`:

```python
def get_stories(tags=None, role=None, stage=None):
    """Return story entries matching all provided filters (AND logic).

    tags:  list of tag strings -- story matches if it has ANY listed tag (OR within tags).
    role:  role slug -- story must include this slug in roles_used.
    stage: accepted for API compatibility; not applied (stories have no stage field).

    Returns empty list on no match or absent library.
    """
    library = _load_library()
    results = library.get("stories", [])
    if tags:
        results = [s for s in results if any(t in s.get("tags", []) for t in tags)]
    if role:
        results = [s for s in results if role in s.get("roles_used", [])]
    return results
```

- [ ] **Step 3.4: Run all tests -- confirm they pass**

```bash
python -m pytest tests/test_interview_library_parser.py -v
```

Expected: 15 passed.

---

### Task 4: Implement get_gap_responses and get_questions with their tests

**Files:**
- Modify: `scripts/interview_library_parser.py`
- Modify: `tests/test_interview_library_parser.py`

- [ ] **Step 4.1: Append get_gap_responses and get_questions tests**

Add to `tests/test_interview_library_parser.py`:

```python
# ── get_gap_responses ─────────────────────────────────────────────────────────

def test_get_gap_responses_returns_all_when_no_filters(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    assert len(ilp.get_gap_responses()) == 1


def test_get_gap_responses_filters_by_gap_label(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    result = ilp.get_gap_responses(gap_label="IP Networking Expertise")
    assert len(result) == 1
    assert result[0]["id"] == "ip-networking-expertise"


def test_get_gap_responses_label_match_is_case_insensitive(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    result = ilp.get_gap_responses(gap_label="ip networking expertise")
    assert len(result) == 1


def test_get_gap_responses_no_match_returns_empty(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    assert ilp.get_gap_responses(gap_label="Nonexistent Gap") == []


def test_get_gap_responses_filters_by_tag(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    result = ilp.get_gap_responses(tags=["domain-gap"])
    assert len(result) == 1


def test_get_gap_responses_filters_by_role(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    result = ilp.get_gap_responses(role="Viasat_SE_IS")
    assert len(result) == 1


def test_get_gap_responses_returns_empty_when_library_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(ilp, "LIBRARY_PATH", str(tmp_path / "missing.json"))
    assert ilp.get_gap_responses() == []


# ── get_questions ─────────────────────────────────────────────────────────────

def test_get_questions_returns_all_when_no_filters(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    assert len(ilp.get_questions()) == 2


def test_get_questions_filters_by_stage(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    result = ilp.get_questions(stage="hiring_manager")
    assert len(result) == 1
    assert result[0]["stage"] == "hiring_manager"


def test_get_questions_filters_by_tag(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    result = ilp.get_questions(tags=["integration"])
    assert len(result) == 1
    assert result[0]["id"] == "where-are-integration-problems"


def test_get_questions_filters_by_stage_and_tag(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    result = ilp.get_questions(stage="team_panel", tags=["technical-credibility"])
    assert len(result) == 1


def test_get_questions_stage_and_tag_no_match(tmp_path, monkeypatch):
    _write_library(tmp_path, _sample_library(), monkeypatch)
    result = ilp.get_questions(stage="recruiter", tags=["mbse"])
    assert result == []


def test_get_questions_returns_empty_when_library_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(ilp, "LIBRARY_PATH", str(tmp_path / "missing.json"))
    assert ilp.get_questions(stage="hiring_manager") == []
```

- [ ] **Step 4.2: Run tests -- confirm new tests fail**

```bash
python -m pytest tests/test_interview_library_parser.py -v 2>&1 | tail -10
```

Expected: 14 new failures.

- [ ] **Step 4.3: Append get_gap_responses and get_questions to scripts/interview_library_parser.py**

Add after `get_stories()`:

```python
def get_gap_responses(tags=None, role=None, gap_label=None):
    """Return gap response entries matching all provided filters (AND logic).

    tags:      list of tag strings -- OR match within tags.
    role:      role slug -- must appear in roles_used.
    gap_label: case-insensitive exact match on gap_label field.

    Returns empty list on no match or absent library.
    """
    library = _load_library()
    results = library.get("gap_responses", [])
    if tags:
        results = [g for g in results if any(t in g.get("tags", []) for t in tags)]
    if role:
        results = [g for g in results if role in g.get("roles_used", [])]
    if gap_label:
        norm = gap_label.lower().strip()
        results = [g for g in results
                   if g.get("gap_label", "").lower().strip() == norm]
    return results


def get_questions(tags=None, role=None, stage=None):
    """Return question entries matching all provided filters (AND logic).

    tags:  list of tag strings -- OR match within tags.
    role:  role slug -- must appear in roles_used.
    stage: exact match on stage field (recruiter / hiring_manager / team_panel).

    Returns empty list on no match or absent library.
    """
    library = _load_library()
    results = library.get("questions", [])
    if tags:
        results = [q for q in results if any(t in q.get("tags", []) for t in tags)]
    if role:
        results = [q for q in results if role in q.get("roles_used", [])]
    if stage:
        results = [q for q in results if q.get("stage") == stage]
    return results
```

- [ ] **Step 4.4: Run all tests -- confirm they pass**

```bash
python -m pytest tests/test_interview_library_parser.py -v
```

Expected: 29 passed.

- [ ] **Step 4.5: Syntax check**

```bash
python -m py_compile scripts/interview_library_parser.py && echo OK
```

- [ ] **Step 4.6: Commit Session A**

```bash
git add scripts/interview_library_parser.py tests/test_interview_library_parser.py
git commit -m "Add interview_library_parser.py: init, load, get_stories/gaps/questions (29 tests)"
```

---

## ══════════════════════════════════════════════════════
## RECOMMENDED BREAK POINT -- END OF SESSION A
##
## Session A is complete and self-contained.
## Session B (below) depends on Session A but is
## substantially more complex (docx parsing).
##
## For a fresh CC instance starting Session B, provide:
##   - CLAUDE.md
##   - docs/features/phase5-workshop-capture/proposal.md
##   - docs/superpowers/plans/2026-04-15-workshop-capture.md  (this file)
##   - scripts/interview_library_parser.py  (the Session A output)
##   - scripts/phase5_interview_prep.py  (to understand docx structure)
##   - tests/test_phase5_thankyou.py  (test pattern reference)
## ══════════════════════════════════════════════════════

---

## ═══════════════════════════════════════════
## SESSION B: Workshop Capture Script
## ═══════════════════════════════════════════

**Before starting Session B:** Verify Session A tests pass.
```bash
python -m pytest tests/test_interview_library_parser.py -v
```
Expected: 29 passed. Do not proceed if any fail.

---

### Task 5: Capture script skeleton -- argparse, docx location, paragraph extraction

**Files:**
- Create: `scripts/phase5_workshop_capture.py`
- Create: `tests/test_phase5_workshop_capture.py`

- [ ] **Step 5.1: Write failing tests for argparse and docx location**

Create `tests/test_phase5_workshop_capture.py`:

```python
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
```

- [ ] **Step 5.2: Run tests -- confirm they fail**

```bash
python -m pytest tests/test_phase5_workshop_capture.py -v 2>&1 | head -15
```

Expected: `ModuleNotFoundError` -- script does not exist yet.

- [ ] **Step 5.3: Write scripts/phase5_workshop_capture.py -- skeleton**

```python
# ==============================================
# phase5_workshop_capture.py
# Parses a workshopped interview prep .docx and
# writes durable content into interview_library.json.
#
# Reads:  data/job_packages/[role]/interview_prep_[stage].docx
# Writes: data/interview_library.json (appends / updates)
#
# Usage:
#   python scripts/phase5_workshop_capture.py \
#     --role Viasat_SE_IS --stage hiring_manager
# ==============================================

import os
import sys
import json
import re
import argparse
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.interview_library_parser import (
    LIBRARY_PATH, TAGS_PATH, init_library, load_tags, _load_library
)

JOBS_PACKAGES_DIR = "data/job_packages"

# ── Tag keyword map for auto-suggestion ──────────────────────────────────────
# Keys match controlled vocabulary in interview_library_tags.json.
# Values are substrings to search in lower-cased content text.

TAG_KEYWORDS = {
    "leadership":            ["led ", "lead ", "managed", "directed", "ownership"],
    "cross-functional":      ["cross-functional", "cross functional", "multi-team", "cross-org"],
    "technical-credibility": ["architecture", "designed", "implemented", "technical review"],
    "ambiguity":             ["ambiguous", "ambiguity", "unclear", "undefined", "pivoted"],
    "stakeholder-management":["stakeholder", "customer", "sponsor", "executive brief"],
    "program-delivery":      ["milestone", "schedule", "delivery", "deadline", "cdrl"],
    "systems-engineering":   ["systems engineering", "se process", "v&v", "verification"],
    "communication":         ["briefed", "presented", "communicated", "weekly report"],
    "conflict-resolution":   ["conflict", "disagreement", "resolved tension", "mediated"],
    "domain-gap":            ["gap in", "limited experience", "new to", "hadn't used"],
    "tools-gap":             ["tool gap", "no experience with", "haven't used"],
    "clearance":             ["clearance", "ts/sci", "secret", "cleared"],
    "salary":                ["salary", "compensation", "offer range"],
    "culture-fit":           ["culture", "team environment", "values alignment"],
    "mbse":                  ["mbse", "model-based", "sysml", "cameo", "doors", "magic draw"],
    "requirements-analysis": ["requirements", "srs", "conops", "specification"],
    "integration":           ["integration", "interface", "icd", "ato"],
    "v-and-v":               ["v&v", "verification", "validation", "qualification"],
    "architecture":          ["architecture", "design pattern", "system design", "framework"],
    "domain-translation":    ["domain translation", "bridging", "translat"],
}


# ==============================================
# ARGPARSE
# ==============================================

def build_parser():
    parser = argparse.ArgumentParser(description="Phase 5 Workshop Capture")
    parser.add_argument("--role", required=True,
                        help="Role package folder name (e.g. Viasat_SE_IS)")
    parser.add_argument("--stage", required=True,
                        help="Interview stage (e.g. hiring_manager, team_panel)")
    return parser


# ==============================================
# DOCX LOCATION
# ==============================================

def _locate_docx(role, stage):
    """Return path to workshopped .docx, or sys.exit with clear error."""
    path = os.path.join(JOBS_PACKAGES_DIR, role, f"interview_prep_{stage}.docx")
    if not os.path.exists(path):
        print(f"\nERROR: Workshopped .docx not found: {path}")
        print("Generate and workshop interview prep before running capture.")
        sys.exit(1)
    return path
```

- [ ] **Step 5.4: Run tests -- confirm they pass**

```bash
python -m pytest tests/test_phase5_workshop_capture.py -v
```

Expected: 5 passed.

---

### Task 6: Docx paragraph extraction and section splitting

**Files:**
- Modify: `scripts/phase5_workshop_capture.py`
- Modify: `tests/test_phase5_workshop_capture.py`

The extract function returns a list of `(text, style_name, is_italic)` tuples -- one per non-blank paragraph. Section splitter then divides this list into story_bank, gap_prep, and questions buckets.

- [ ] **Step 6.1: Write failing tests for extraction and section splitting**

Add to `tests/test_phase5_workshop_capture.py`:

```python
# ── _extract_docx_paragraphs ──────────────────────────────────────────────────
# These tests use real (minimal) docx files built with python-docx.

def _make_minimal_docx(tmp_path, paragraphs):
    """Build a minimal .docx with the given (text, bold, italic) tuples."""
    from docx import Document
    doc = Document()
    for text, bold, italic in paragraphs:
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
    path = tmp_path / "test.docx"
    doc.save(str(path))
    return str(path)


def test_extract_skips_blank_paragraphs(tmp_path):
    path = _make_minimal_docx(tmp_path, [
        ("Hello", False, False),
        ("", False, False),
        ("World", False, False),
    ])
    result = wc._extract_docx_paragraphs(path)
    assert len(result) == 2
    assert result[0][0] == "Hello"
    assert result[1][0] == "World"


def test_extract_detects_italic_paragraphs(tmp_path):
    path = _make_minimal_docx(tmp_path, [
        ("Normal line", False, False),
        ("Italic coaching line", False, True),
    ])
    result = wc._extract_docx_paragraphs(path)
    assert result[0][2] is False   # not italic
    assert result[1][2] is True    # italic


# ── _split_sections ───────────────────────────────────────────────────────────

def _paras(texts):
    """Helper: build paragraph tuples with default style and not italic."""
    return [(t, "Normal", False) for t in texts]


def test_split_sections_finds_story_bank():
    paras = _paras([
        "Interview Prep Package",
        "Story Bank",
        "STORY 1 -- MBSE:",
        "Situation: context here.",
        "Gap Preparation",
        "GAP 1 -- Networking [REQUIRED]:",
    ])
    sections = wc._split_sections(paras)
    assert any("STORY 1" in t for t, _, _ in sections["story_bank"])


def test_split_sections_finds_gap_prep():
    paras = _paras([
        "Story Bank",
        "STORY 1 -- MBSE:",
        "Gap Preparation",
        "GAP 1 -- Networking [REQUIRED]:",
        "Honest answer: here.",
    ])
    sections = wc._split_sections(paras)
    assert any("GAP 1" in t for t, _, _ in sections["gap_prep"])


def test_split_sections_finds_questions():
    paras = _paras([
        "Gap Preparation",
        "GAP 1 -- Topic [REQUIRED]:",
        "Questions to Ask",
        "1. What does success look like at 6 months?",
    ])
    sections = wc._split_sections(paras)
    assert any("success" in t for t, _, _ in sections["questions"])


def test_split_sections_excludes_other_sections():
    paras = _paras([
        "Company Role Brief",
        "Company overview here.",
        "Story Bank",
        "STORY 1 -- MBSE:",
    ])
    sections = wc._split_sections(paras)
    assert not any("overview" in t for t, _, _ in sections["story_bank"])
```

- [ ] **Step 6.2: Run tests -- confirm new tests fail**

```bash
python -m pytest tests/test_phase5_workshop_capture.py -v 2>&1 | tail -15
```

Expected: failures on extract and split tests.

- [ ] **Step 6.3: Add _extract_docx_paragraphs and _split_sections to capture script**

Add after `_locate_docx`:

```python
# ==============================================
# DOCX EXTRACTION
# ==============================================

def _extract_docx_paragraphs(docx_path):
    """
    Extract paragraphs from docx as list of (text, style_name, is_italic) tuples.
    Blank paragraphs are skipped.
    is_italic is True when all non-blank runs in the paragraph are italic.
    """
    from docx import Document
    doc = Document(docx_path)
    result = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = para.style.name
        non_blank_runs = [r for r in para.runs if r.text.strip()]
        is_italic = bool(non_blank_runs) and all(r.italic for r in non_blank_runs)
        result.append((text, style, is_italic))
    return result


def _split_sections(paragraphs):
    """
    Divide paragraph list into story_bank, gap_prep, questions buckets.
    Detection uses case-insensitive substring match on paragraph text.
    Paragraphs in other sections (Company Brief, Introduce Yourself, etc.)
    are assigned to no bucket and discarded.
    """
    SECTION_MARKERS = {
        "story_bank":  ["STORY BANK"],
        "gap_prep":    ["GAP PREPARATION"],
        "questions":   ["QUESTIONS TO ASK"],
        "other":       ["COMPANY", "ROLE BRIEF", "INTRODUCE YOURSELF",
                        "SALARY", "END OF", "INTERVIEW PREP PACKAGE",
                        "CONTINUITY"],
    }
    sections = {"story_bank": [], "gap_prep": [], "questions": []}
    current = None

    for text, style, is_italic in paragraphs:
        upper = text.upper()
        matched_section = False
        for key, markers in SECTION_MARKERS.items():
            if any(m in upper for m in markers):
                current = None if key == "other" else key
                matched_section = True
                break
        if not matched_section and current in sections:
            sections[current].append((text, style, is_italic))

    return sections
```

- [ ] **Step 6.4: Run all tests -- confirm they pass**

```bash
python -m pytest tests/test_phase5_workshop_capture.py -v
```

Expected: 12 passed.

---

### Task 7: Story block parser

**Files:**
- Modify: `scripts/phase5_workshop_capture.py`
- Modify: `tests/test_phase5_workshop_capture.py`

- [ ] **Step 7.1: Write failing story parsing tests**

Add to `tests/test_phase5_workshop_capture.py`:

```python
# ── _parse_stories ────────────────────────────────────────────────────────────

def _story_paras(lines):
    """Build paragraph tuples for story bank content."""
    return [(line, "Normal", False) for line in lines]


def test_parse_stories_extracts_employer_title_dates():
    paras = _story_paras([
        "STORY 1 -- MBSE Toolchain [Systems Engineering]:",
        "Employer: G2 OPS | Systems Engineer | 2021-2023",
        "Situation: Context here.",
        "Task: What needed doing.",
        "Action: What I did.",
        "Result: The outcome.",
    ])
    stories = wc._parse_stories(paras)
    assert len(stories) == 1
    assert stories[0]["employer"] == "G2 OPS"
    assert stories[0]["title_held"] == "Systems Engineer"
    assert stories[0]["dates"] == "2021-2023"


def test_parse_stories_extracts_star_components():
    paras = _story_paras([
        "STORY 1 -- Requirement:",
        "Employer: ACME | Engineer | 2022-2023",
        "Situation: Sat text.",
        "Task: Task text.",
        "Action: Action text.",
        "Result: Result text.",
    ])
    s = wc._parse_stories(paras)[0]
    assert s["situation"] == "Sat text."
    assert s["task"] == "Task text."
    assert s["action"] == "Action text."
    assert s["result"] == "Result text."


def test_parse_stories_extracts_if_probed():
    paras = _story_paras([
        "STORY 1 -- Requirement:",
        "Employer: ACME | Engineer | 2022",
        "Situation: S.", "Task: T.", "Action: A.", "Result: R.",
        "If probed: One more sentence.",
    ])
    s = wc._parse_stories(paras)[0]
    assert s["if_probed"] == "One more sentence."


def test_parse_stories_if_probed_none_when_absent():
    paras = _story_paras([
        "STORY 1 -- Requirement:",
        "Employer: ACME | Engineer | 2022",
        "Situation: S.", "Task: T.", "Action: A.", "Result: R.",
    ])
    s = wc._parse_stories(paras)[0]
    assert s["if_probed"] is None


def test_parse_stories_skips_italic_paragraphs():
    paras = [
        ("STORY 1 -- Requirement:", "Normal", False),
        ("Employer: ACME | Engineer | 2022", "Normal", False),
        ("Signals: do not include this line.", "Normal", True),   # italic
        ("Situation: Real situation.", "Normal", False),
        ("Task: T.", "Normal", False),
        ("Action: A.", "Normal", False),
        ("Result: R.", "Normal", False),
    ]
    s = wc._parse_stories(paras)[0]
    assert s["situation"] == "Real situation."


def test_parse_stories_handles_multiple_stories():
    paras = _story_paras([
        "STORY 1 -- First:",
        "Employer: ACME | Eng | 2021",
        "Situation: S1.", "Task: T1.", "Action: A1.", "Result: R1.",
        "STORY 2 -- Second:",
        "Employer: Corp | Arch | 2022",
        "Situation: S2.", "Task: T2.", "Action: A2.", "Result: R2.",
    ])
    stories = wc._parse_stories(paras)
    assert len(stories) == 2
    assert stories[0]["employer"] == "ACME"
    assert stories[1]["employer"] == "Corp"
```

- [ ] **Step 7.2: Run new tests -- confirm they fail**

```bash
python -m pytest tests/test_phase5_workshop_capture.py -k "parse_stories" -v 2>&1 | tail -10
```

Expected: all fail with `AttributeError`.

- [ ] **Step 7.3: Add _parse_stories to scripts/phase5_workshop_capture.py**

```python
# ==============================================
# STORY PARSER
# ==============================================

def _parse_stories(paragraphs):
    """
    Parse story bank paragraphs into a list of story dicts.
    Each dict has: employer, title_held, dates, situation, task,
                   action, result, if_probed, _header (raw story heading).
    Italic paragraphs are skipped (coaching / delivery notes).
    """
    STORY_FIELDS = {
        "Situation:": "situation",
        "Task:":      "task",
        "Action:":    "action",
        "Result:":    "result",
        "If probed:": "if_probed",
    }
    stories = []
    current = None
    current_field = None

    for text, style, is_italic in paragraphs:
        if is_italic:
            continue

        if re.match(r'^STORY\s+\d+\s*[-\u2013]', text, re.IGNORECASE):
            if current:
                stories.append(current)
            current = {
                "employer": "", "title_held": "", "dates": "",
                "situation": "", "task": "", "action": "", "result": "",
                "if_probed": None, "_header": text
            }
            current_field = None
            continue

        if current is None:
            continue

        if text.startswith("Employer:"):
            value = text[len("Employer:"):].strip()
            parts = [p.strip() for p in value.split("|")]
            current["employer"]   = parts[0] if len(parts) > 0 else ""
            current["title_held"] = parts[1] if len(parts) > 1 else ""
            current["dates"]      = parts[2] if len(parts) > 2 else ""
            current_field = None
            continue

        matched = False
        for label, field in STORY_FIELDS.items():
            if text.startswith(label):
                current[field] = text[len(label):].strip()
                current_field = field
                matched = True
                break

        if not matched and current_field:
            # Continuation line for the current field
            if current[current_field] is None:
                current[current_field] = text
            elif current[current_field]:
                current[current_field] += " " + text

    if current:
        stories.append(current)
    return stories
```

- [ ] **Step 7.4: Run all tests -- confirm they pass**

```bash
python -m pytest tests/test_phase5_workshop_capture.py -v
```

Expected: 19 passed.

---

### Task 8: Gap block parser

**Files:**
- Modify: `scripts/phase5_workshop_capture.py`
- Modify: `tests/test_phase5_workshop_capture.py`

- [ ] **Step 8.1: Write failing gap parsing tests**

Add to `tests/test_phase5_workshop_capture.py`:

```python
# ── _parse_gaps ───────────────────────────────────────────────────────────────

def _gap_paras(lines):
    return [(line, "Normal", False) for line in lines]


def test_parse_gaps_extracts_label_and_severity_required():
    paras = _gap_paras([
        "GAP 1 -- IP Networking Expertise [REQUIRED]:",
        "Gap: I have not worked in IP networking.",
        "Honest answer: Direct acknowledgment.",
        "Bridge: Adjacent experience.",
        "Redirect: Strong redirect.",
    ])
    gaps = wc._parse_gaps(paras)
    assert len(gaps) == 1
    assert gaps[0]["gap_label"] == "IP Networking Expertise"
    assert gaps[0]["severity"] == "required"


def test_parse_gaps_extracts_severity_preferred():
    paras = _gap_paras([
        "GAP 1 -- Cameo TWC Experience [PREFERRED]:",
        "Gap: gap text.", "Honest answer: A.", "Bridge: B.", "Redirect: R.",
    ])
    assert wc._parse_gaps(paras)[0]["severity"] == "preferred"


def test_parse_gaps_extracts_triad():
    paras = _gap_paras([
        "GAP 1 -- Topic [REQUIRED]:",
        "Gap: gap text.",
        "Honest answer: Honest text.",
        "Bridge: Bridge text.",
        "Redirect: Redirect text.",
    ])
    g = wc._parse_gaps(paras)[0]
    assert g["honest_answer"] == "Honest text."
    assert g["bridge"] == "Bridge text."
    assert g["redirect"] == "Redirect text."


def test_parse_gaps_excludes_short_tenure_section():
    paras = _gap_paras([
        "SHORT TENURE EXPLANATION:",
        "I left after 8 months because...",
        "GAP 1 -- Networking [REQUIRED]:",
        "Gap: gap text.", "Honest answer: A.", "Bridge: B.", "Redirect: R.",
    ])
    gaps = wc._parse_gaps(paras)
    assert len(gaps) == 1
    assert gaps[0]["gap_label"] == "Networking"


def test_parse_gaps_stops_at_hard_questions():
    paras = _gap_paras([
        "GAP 1 -- Topic [REQUIRED]:",
        "Gap: g.", "Honest answer: A.", "Bridge: B.", "Redirect: R.",
        "HARD QUESTIONS TO PREPARE FOR:",
        "1. Tough question?",
    ])
    gaps = wc._parse_gaps(paras)
    assert len(gaps) == 1


def test_parse_gaps_skips_italic_paragraphs():
    paras = [
        ("GAP 1 -- Topic [REQUIRED]:", "Normal", False),
        ("Coaching note -- do not use.", "Normal", True),
        ("Gap: gap text.", "Normal", False),
        ("Honest answer: A.", "Normal", False),
        ("Bridge: B.", "Normal", False),
        ("Redirect: R.", "Normal", False),
    ]
    gaps = wc._parse_gaps(paras)
    assert len(gaps) == 1
```

- [ ] **Step 8.2: Run new tests -- confirm they fail**

```bash
python -m pytest tests/test_phase5_workshop_capture.py -k "parse_gaps" -v 2>&1 | tail -10
```

- [ ] **Step 8.3: Add _parse_gaps to scripts/phase5_workshop_capture.py**

```python
# ==============================================
# GAP PARSER
# ==============================================

def _parse_gaps(paragraphs):
    """
    Parse gap prep paragraphs into a list of gap response dicts.
    Each dict has: gap_label, severity, honest_answer, bridge, redirect.
    Skips: italic paragraphs, SHORT TENURE section.
    Stops at: HARD QUESTIONS section.
    """
    GAP_FIELDS = {
        "Honest answer:": "honest_answer",
        "Bridge:":        "bridge",
        "Redirect:":      "redirect",
    }
    gaps = []
    current = None
    current_field = None
    in_short_tenure = False

    for text, style, is_italic in paragraphs:
        if is_italic:
            continue
        upper = text.upper()
        if "SHORT TENURE" in upper:
            in_short_tenure = True
            current = None
            continue
        if "HARD QUESTIONS" in upper:
            break
        if re.match(r'^GAP\s+\d+\s*[-\u2013]', text, re.IGNORECASE):
            in_short_tenure = False
            if current:
                gaps.append(current)
            severity = "preferred" if "[PREFERRED]" in upper else "required"
            label_match = re.match(
                r'^GAP\s+\d+\s*[-\u2013]\s*(.+?)(?:\s*\[(?:REQUIRED|PREFERRED)\])?:?$',
                text, re.IGNORECASE
            )
            gap_label = label_match.group(1).strip() if label_match else text
            current = {
                "gap_label": gap_label, "severity": severity,
                "honest_answer": "", "bridge": "", "redirect": "",
            }
            current_field = None
            continue

        if in_short_tenure or current is None:
            continue
        if text.startswith("Gap:"):
            current_field = None  # Skip the Gap: line itself
            continue

        matched = False
        for label, field in GAP_FIELDS.items():
            if text.startswith(label):
                current[field] = text[len(label):].strip()
                current_field = field
                matched = True
                break
        if not matched and current_field:
            if current[current_field]:
                current[current_field] += " " + text

    if current:
        gaps.append(current)
    return gaps
```

- [ ] **Step 8.4: Run all tests -- confirm they pass**

```bash
python -m pytest tests/test_phase5_workshop_capture.py -v
```

Expected: 26 passed.

---

### Task 9: Question block parser

**Files:**
- Modify: `scripts/phase5_workshop_capture.py`
- Modify: `tests/test_phase5_workshop_capture.py`

- [ ] **Step 9.1: Write failing question parsing tests**

Add to `tests/test_phase5_workshop_capture.py`:

```python
# ── _parse_questions ──────────────────────────────────────────────────────────

def test_parse_questions_extracts_question_text():
    paras = [(
        "1. What does success look like at 6 months? Signals you're thinking about impact.",
        "Normal", False
    )]
    questions = wc._parse_questions(paras, "hiring_manager")
    assert len(questions) == 1
    assert questions[0]["text"] == "What does success look like at 6 months?"
    assert questions[0]["stage"] == "hiring_manager"


def test_parse_questions_strips_rationale():
    paras = [(
        "2. Where are the hard interface problems right now? This signals peer credibility.",
        "Normal", False
    )]
    q = wc._parse_questions(paras, "team_panel")[0]
    assert q["text"].endswith("?")
    assert "credibility" not in q["text"]


def test_parse_questions_skips_italic():
    paras = [
        ("1. Real question?", "Normal", False),
        ("Coaching note.", "Normal", True),
        ("2. Another question?", "Normal", False),
    ]
    questions = wc._parse_questions(paras, "recruiter")
    assert len(questions) == 2


def test_parse_questions_returns_empty_when_no_numbered_items():
    paras = [("Not a numbered item.", "Normal", False)]
    assert wc._parse_questions(paras, "hiring_manager") == []


def test_closing_question_excluded():
    paras = [
        ("1. What does success look like at 6 months?", "Normal", False),
        ("Based on our conversation, is there anything that gives you pause about my fit?",
         "Normal", False),
    ]
    questions = wc._parse_questions(paras, "hiring_manager")
    assert len(questions) == 1
    assert not any("Based on our conversation" in q["text"] for q in questions)
```

- [ ] **Step 9.2: Run new tests -- confirm they fail**

```bash
python -m pytest tests/test_phase5_workshop_capture.py -k "parse_questions" -v 2>&1 | tail -8
```

- [ ] **Step 9.3: Add _parse_questions to scripts/phase5_workshop_capture.py**

```python
# ==============================================
# QUESTION PARSER
# ==============================================

def _parse_questions(paragraphs, stage):
    """
    Parse questions section paragraphs into a list of question dicts.
    Each dict has: stage, text (question only, rationale stripped), category=None.
    Extracts numbered items (1. ...) only.
    Strips rationale text after the closing "?".
    Italic paragraphs are skipped.
    """
    questions = []
    for text, style, is_italic in paragraphs:
        if is_italic:
            continue
        if not re.match(r'^\d+\.', text):
            continue
        # Strip number prefix
        text_no_num = re.sub(r'^\d+\.\s*', '', text).strip()
        # Take only up to and including the first "?"
        q_match = re.search(r'^(.*?\?)', text_no_num)
        if not q_match:
            continue
        q_text = q_match.group(1).strip()
        questions.append({"stage": stage, "text": q_text, "category": None})
    return questions
```

- [ ] **Step 9.4: Run all tests -- confirm they pass**

```bash
python -m pytest tests/test_phase5_workshop_capture.py -v
```

Expected: 30 passed.

---

### Task 10: Tag suggestion, ID generation, duplicate detection, library write, main(), full integration tests

**Files:**
- Modify: `scripts/phase5_workshop_capture.py`
- Modify: `tests/test_phase5_workshop_capture.py`

This is the most complex task -- break into sub-steps.

- [ ] **Step 10.1: Write failing tests for tag suggestion, ID generation, duplicate detection**

Add to `tests/test_phase5_workshop_capture.py`:

```python
# ── Tag suggestion ────────────────────────────────────────────────────────────

def test_suggest_tags_matches_keywords(tmp_path, monkeypatch):
    import scripts.interview_library_parser as ilp
    tags_path = tmp_path / "tags.json"
    tags_path.write_text(json.dumps({"tags": list(wc.TAG_KEYWORDS.keys())}))
    monkeypatch.setattr(ilp, "TAGS_PATH", str(tags_path))
    text = "I led a cross-functional team delivering MBSE toolchain improvements."
    suggested = wc._suggest_tags(text)
    assert "leadership" in suggested
    assert "cross-functional" in suggested
    assert "mbse" in suggested


def test_suggest_tags_unknown_tag_not_in_result():
    text = "Nothing here matches any tag."
    suggested = wc._suggest_tags(text)
    assert suggested == []


# ── ID generation ─────────────────────────────────────────────────────────────

def test_make_story_id_slugifies_employer():
    slug = wc._make_story_id("G2 OPS", ["mbse"])
    assert slug == "g2-ops-mbse"


def test_make_gap_id_slugifies_label():
    slug = wc._make_gap_id("IP Networking Expertise")
    assert slug == "ip-networking-expertise"


def test_make_question_id_uses_first_60_chars():
    text = "What does success look like at 6 months?"
    slug = wc._make_question_id(text)
    assert len(slug) <= 60
    assert "success" in slug


# ── Duplicate detection ───────────────────────────────────────────────────────

def test_find_duplicate_story_matches_employer_and_tag():
    library = {
        "stories": [{"id": "g2-ops-mbse", "employer": "G2 OPS", "tags": ["mbse"],
                     "roles_used": ["OldRole"]}],
        "gap_responses": [], "questions": []
    }
    result = wc._find_duplicate_story(library, "G2 OPS", "mbse")
    assert result is not None
    assert result["id"] == "g2-ops-mbse"


def test_find_duplicate_story_no_match():
    library = {"stories": [], "gap_responses": [], "questions": []}
    assert wc._find_duplicate_story(library, "ACME", "leadership") is None


def test_find_duplicate_gap_case_insensitive():
    library = {
        "stories": [], "questions": [],
        "gap_responses": [{"id": "ip-networking", "gap_label": "IP Networking",
                           "roles_used": []}]
    }
    assert wc._find_duplicate_gap(library, "ip networking") is not None


# ── Skip path: roles_used updated ────────────────────────────────────────────

def test_skip_updates_roles_used(tmp_path, monkeypatch):
    library = {
        "stories": [{"id": "g2-ops-mbse", "employer": "G2 OPS", "tags": ["mbse"],
                     "roles_used": ["OldRole"]}],
        "gap_responses": [], "questions": []
    }
    lib_path = _seed_library(tmp_path, library, monkeypatch)
    wc._skip_update_roles(library["stories"][0], "NewRole", library, "stories")
    wc._write_library(library)
    saved = json.loads(lib_path.read_text())
    assert "NewRole" in saved["stories"][0]["roles_used"]
    assert "OldRole" in saved["stories"][0]["roles_used"]


# ── Overwrite path: entry replaced, roles_used merged ────────────────────────

def test_overwrite_merges_roles_used(tmp_path, monkeypatch):
    library = {
        "stories": [{"id": "g2-ops-mbse", "employer": "G2 OPS", "tags": ["mbse"],
                     "roles_used": ["OldRole"]}],
        "gap_responses": [], "questions": []
    }
    lib_path = _seed_library(tmp_path, library, monkeypatch)
    new_entry = {"id": "g2-ops-mbse", "employer": "G2 OPS", "tags": ["mbse"],
                 "roles_used": ["NewRole"]}
    wc._overwrite_entry(library["stories"][0], new_entry, library, "stories")
    wc._write_library(library)
    saved = json.loads(lib_path.read_text())
    assert "OldRole" in saved["stories"][0]["roles_used"]
    assert "NewRole" in saved["stories"][0]["roles_used"]
```

- [ ] **Step 10.2: Run new tests -- confirm they fail**

```bash
python -m pytest tests/test_phase5_workshop_capture.py -k "suggest_tags or make_story or make_gap or make_question or duplicate or skip_update or overwrite" -v 2>&1 | tail -15
```

- [ ] **Step 10.3: Add helper functions to scripts/phase5_workshop_capture.py**

```python
# ==============================================
# TAG SUGGESTION AND ID GENERATION
# ==============================================

def _suggest_tags(text):
    """Return list of tags from controlled vocabulary whose keywords appear in text."""
    vocabulary = load_tags()
    text_lower = text.lower()
    return [
        tag for tag, keywords in TAG_KEYWORDS.items()
        if tag in vocabulary and any(kw in text_lower for kw in keywords)
    ]


def _make_story_id(employer, tags):
    """Generate a unique slug from employer name and primary tag."""
    emp = re.sub(r'[^a-z0-9]+', '-', employer.lower()).strip('-')
    tag = tags[0] if tags else "story"
    return f"{emp}-{tag}"[:60]


def _make_gap_id(gap_label):
    """Generate a unique slug from gap label."""
    return re.sub(r'[^a-z0-9]+', '-', gap_label.lower()).strip('-')[:60]


def _make_question_id(text):
    """Generate a unique slug from first 60 chars of question text."""
    return re.sub(r'[^a-z0-9]+', '-', text.lower())[:60].strip('-')


# ==============================================
# DUPLICATE DETECTION
# ==============================================

def _find_duplicate_story(library, employer, primary_tag):
    """Return existing story entry matching employer + primary_tag, or None."""
    for s in library.get("stories", []):
        if (s.get("employer", "").lower() == employer.lower() and
                primary_tag in s.get("tags", [])):
            return s
    return None


def _find_duplicate_gap(library, gap_label):
    """Return existing gap entry matching gap_label (case-insensitive), or None."""
    norm = gap_label.lower().strip()
    for g in library.get("gap_responses", []):
        if g.get("gap_label", "").lower().strip() == norm:
            return g
    return None


def _find_duplicate_question(library, text):
    """Return existing question entry matching first 60 chars of text, or None."""
    prefix = text[:60].lower()
    for q in library.get("questions", []):
        if q.get("text", "")[:60].lower() == prefix:
            return q
    return None


# ==============================================
# LIBRARY WRITE HELPERS
# ==============================================

def _write_library(library):
    """Write library dict to LIBRARY_PATH."""
    with open(LIBRARY_PATH, "w", encoding="utf-8") as f:
        json.dump(library, f, indent=2, ensure_ascii=False)


def _skip_update_roles(existing_entry, role, library, section_key):
    """On skip: add role to roles_used if not already present. Mutates library in place."""
    if role not in existing_entry.get("roles_used", []):
        existing_entry.setdefault("roles_used", []).append(role)
    # Ensure the library dict reflects the mutation
    for i, entry in enumerate(library[section_key]):
        if entry.get("id") == existing_entry["id"]:
            library[section_key][i] = existing_entry
            break


def _overwrite_entry(existing_entry, new_entry, library, section_key):
    """On overwrite: replace entry; merge roles_used from both. Mutates library in place."""
    merged_roles = list(set(
        existing_entry.get("roles_used", []) + new_entry.get("roles_used", [])
    ))
    new_entry["roles_used"] = merged_roles
    for i, entry in enumerate(library[section_key]):
        if entry.get("id") == existing_entry["id"]:
            library[section_key][i] = new_entry
            break
```

- [ ] **Step 10.4: Run tests -- confirm they pass**

```bash
python -m pytest tests/test_phase5_workshop_capture.py -v
```

Expected: 45 passed.

- [ ] **Step 10.5: Add _confirm_tags, _build_entry functions, and main() to scripts/phase5_workshop_capture.py**

```python
# ==============================================
# ENTRY BUILDERS
# ==============================================

def _build_story_entry(raw, tags, role, today):
    """Convert a parsed story dict to a library-ready entry."""
    return {
        "id":          _make_story_id(raw["employer"], tags),
        "title":       raw["_header"],
        "tags":        tags,
        "employer":    raw["employer"],
        "title_held":  raw["title_held"],
        "dates":       raw["dates"],
        "situation":   raw["situation"],
        "task":        raw["task"],
        "action":      raw["action"],
        "result":      raw["result"],
        "if_probed":   raw["if_probed"],
        "notes":       None,
        "source":      "workshopped",
        "roles_used":  [role],
        "last_updated": today,
    }


def _build_gap_entry(raw, tags, role, today):
    """Convert a parsed gap dict to a library-ready entry."""
    return {
        "id":           _make_gap_id(raw["gap_label"]),
        "gap_label":    raw["gap_label"],
        "severity":     raw["severity"],
        "tags":         tags,
        "honest_answer": raw["honest_answer"],
        "bridge":       raw["bridge"],
        "redirect":     raw["redirect"],
        "notes":        None,
        "source":       "workshopped",
        "roles_used":   [role],
        "last_updated": today,
    }


def _build_question_entry(raw, tags, role, today):
    """Convert a parsed question dict to a library-ready entry."""
    category = tags[0] if tags else "general"
    return {
        "id":          _make_question_id(raw["text"]),
        "stage":       raw["stage"],
        "category":    category,
        "text":        raw["text"],
        "tags":        tags,
        "notes":       None,
        "source":      "workshopped",
        "roles_used":  [role],
        "last_updated": today,
    }


def _confirm_tags(content_text, label):
    """
    Suggest tags for an entry; prompt user to accept or override.
    Returns final confirmed list of tags.
    Unknown tags produce a warning but are accepted.
    """
    vocabulary = load_tags()
    suggested = _suggest_tags(content_text)
    if suggested:
        print(f"  Suggested tags for {label}: {', '.join(suggested)}")
    else:
        print(f"  No tags auto-suggested for {label}.")
    raw = input(
        "  Press Enter to accept, or type comma-separated tags: "
    ).strip()
    if not raw:
        tags = suggested
    else:
        tags = [t.strip() for t in raw.split(",") if t.strip()]
    unknown = [t for t in tags if t not in vocabulary]
    for t in unknown:
        print(f"  WARNING: '{t}' is not in the tag vocabulary -- accepted anyway.")
    return tags


def _handle_duplicate(existing, new_entry, library, section_key, role, label):
    """
    Handle a duplicate entry. Prompt: skip / overwrite / rename.
    Returns True if entry was written (overwrite or rename), False if skipped.
    """
    answer = input(
        f"  Entry '{existing['id']}' already exists. Skip / overwrite / rename? (s/o/r): "
    ).strip().lower()
    if answer == "s":
        _skip_update_roles(existing, role, library, section_key)
        print(f"  Skipped {label} -- roles_used updated.")
        return False
    elif answer == "o":
        _overwrite_entry(existing, new_entry, library, section_key)
        print(f"  Overwrote {label}.")
        return True
    elif answer == "r":
        new_id = input("  Enter new ID: ").strip()
        new_entry["id"] = new_id
        library[section_key].append(new_entry)
        print(f"  Added as new entry '{new_id}'.")
        return True
    else:
        print("  Invalid choice -- skipping.")
        _skip_update_roles(existing, role, library, section_key)
        return False


# ==============================================
# MAIN
# ==============================================

def main():
    args = build_parser().parse_args()
    role = args.role
    stage = args.stage
    today = str(date.today())

    print("=" * 60)
    print("PHASE 5 \u2013 WORKSHOP CAPTURE")
    print("=" * 60)
    print(f"Role:  {role}")
    print(f"Stage: {stage}")

    docx_path = _locate_docx(role, stage)
    print(f"\nReading: {docx_path}")

    paragraphs = _extract_docx_paragraphs(docx_path)
    sections = _split_sections(paragraphs)

    raw_stories   = _parse_stories(sections["story_bank"])
    raw_gaps      = _parse_gaps(sections["gap_prep"])
    raw_questions = _parse_questions(sections["questions"], stage)

    print(f"\nFound: {len(raw_stories)} stories, "
          f"{len(raw_gaps)} gap responses, "
          f"{len(raw_questions)} questions")

    # ── Tag assignment ──────────────────────────────────────────────────────
    print("\n-- Tag Assignment --")
    story_entries = []
    for i, raw in enumerate(raw_stories):
        label = f"story {i+1} ({raw['employer']})"
        content = " ".join([raw["situation"], raw["task"], raw["action"], raw["result"]])
        tags = _confirm_tags(content, label)
        story_entries.append(_build_story_entry(raw, tags, role, today))

    gap_entries = []
    for i, raw in enumerate(raw_gaps):
        label = f"gap '{raw['gap_label']}'"
        content = " ".join([raw["honest_answer"], raw["bridge"], raw["redirect"]])
        tags = _confirm_tags(content, label)
        gap_entries.append(_build_gap_entry(raw, tags, role, today))

    question_entries = []
    for i, raw in enumerate(raw_questions):
        label = f"question {i+1}"
        tags = _confirm_tags(raw["text"], label)
        question_entries.append(_build_question_entry(raw, tags, role, today))

    # ── Summary and confirmation ────────────────────────────────────────────
    total = len(story_entries) + len(gap_entries) + len(question_entries)
    print(f"\nReady to write {len(story_entries)} stories, "
          f"{len(gap_entries)} gap responses, "
          f"{len(question_entries)} questions to interview_library.json.")
    answer = input(f"Write {total} entries? (y/n): ").strip().lower()
    if answer != "y":
        print("Cancelled -- no file written.")
        sys.exit(0)

    # ── Write with duplicate handling ───────────────────────────────────────
    init_library()
    library = _load_library()
    written = skipped = 0

    for entry in story_entries:
        dup = _find_duplicate_story(library, entry["employer"], entry["tags"][0] if entry["tags"] else "")
        if dup:
            if _handle_duplicate(dup, entry, library, "stories", role, entry["id"]):
                written += 1
            else:
                skipped += 1
        else:
            library["stories"].append(entry)
            written += 1

    for entry in gap_entries:
        dup = _find_duplicate_gap(library, entry["gap_label"])
        if dup:
            if _handle_duplicate(dup, entry, library, "gap_responses", role, entry["id"]):
                written += 1
            else:
                skipped += 1
        else:
            library["gap_responses"].append(entry)
            written += 1

    for entry in question_entries:
        dup = _find_duplicate_question(library, entry["text"])
        if dup:
            if _handle_duplicate(dup, entry, library, "questions", role, entry["id"]):
                written += 1
            else:
                skipped += 1
        else:
            library["questions"].append(entry)
            written += 1

    _write_library(library)

    print(f"\n{'=' * 60}")
    print(f"Written: {written} entries")
    if skipped:
        print(f"Skipped: {skipped} (existing entries; roles_used updated)")
    print(f"Library: {LIBRARY_PATH}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 10.6: Syntax check**

```bash
python -m py_compile scripts/phase5_workshop_capture.py && echo OK
```

- [ ] **Step 10.7: Run full test suite**

```bash
python -m pytest tests/test_interview_library_parser.py tests/test_phase5_workshop_capture.py -v 2>&1 | tail -5
```

Expected: all tests pass, zero failures, zero errors.

- [ ] **Step 10.8: Run all project tests -- confirm no regressions**

```bash
python -m pytest -v 2>&1 | tail -10
```

Expected: all prior tests still pass.

- [ ] **Step 10.9: Commit Session B**

```bash
git add scripts/phase5_workshop_capture.py tests/test_phase5_workshop_capture.py
git commit -m "Add phase5_workshop_capture.py: docx parsing, library write, duplicate handling (45 tests)"
```

---

## Self-Review

### Spec Coverage Check

| Spec requirement | Task |
|---|---|
| `interview_library.json` init -- empty arrays, never overwrites | Task 2 |
| Three top-level arrays: stories, gap_responses, questions | Task 1 |
| All story fields (id, title, tags, employer, title_held, dates, STAR, if_probed, notes, source, roles_used, last_updated) | Task 10 (`_build_story_entry`) |
| All gap fields (id, gap_label, severity, tags, honest_answer, bridge, redirect, notes, source, roles_used, last_updated) | Task 10 (`_build_gap_entry`) |
| All question fields (id, stage, category, text, tags, notes, source, roles_used, last_updated) | Task 10 (`_build_question_entry`) |
| `interview_library_tags.json` -- 20 initial tags | Task 1 |
| Unknown tags warn but do not block | Task 10 (`_confirm_tags`) |
| `interview_library_parser.py` -- get_stories, get_gap_responses, get_questions | Tasks 3, 4 |
| AND logic across filters, OR within tags | Tasks 3, 4 |
| Returns empty list (not error) on no match or absent file | Tasks 3, 4 |
| `phase5_workshop_capture.py` -- --role and --stage required | Task 5 |
| Locates docx at `data/job_packages/[role]/interview_prep_[stage].docx` | Task 5 |
| Story block parsing (STORY N -- header, Employer:, STAR, If probed) | Task 7 |
| Strips italic/coaching lines | Tasks 7, 8, 9 |
| Gap block parsing (GAP N --, label, severity, honest_answer, bridge, redirect) | Task 8 |
| Strips SHORT TENURE section | Task 8 |
| Stops at HARD QUESTIONS section | Task 8 |
| Question block parsing (numbered items, strip rationale) | Task 9 |
| Tag auto-suggestion via keyword matching | Task 10 |
| User confirms/overrides tags before write | Task 10 |
| Summary + write confirmation prompt | Task 10 |
| Duplicate detection: story (employer + primary tag), gap (label), question (first 60 chars) | Task 10 |
| Skip path: roles_used updated, entry not replaced | Task 10 |
| Overwrite path: entry replaced, roles_used merged | Task 10 |
| Rename path: new ID prompted, written as new entry | Task 10 |
| `init_library` called before write | Task 10 |
| Entry count printed on completion | Task 10 |
| No-regression: absent library / absent tags file | Tasks 2, 3, 4 (tests cover this) |
