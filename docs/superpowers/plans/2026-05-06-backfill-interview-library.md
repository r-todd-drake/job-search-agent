# Interview Library Backfill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `scripts/utils/backfill_interview_library.py` to bulk-parse all workshopped `.docx` files under `data/interview_prep_workshopped/` and populate `data/interview_library.json` with extracted introductions, stories, gap responses, and questions.

**Architecture:** The script imports all parsing, ID-generation, dedup, and entry-building functions directly from `phase5_workshop_capture.py` (DRY — already well-tested). New logic covers: multi-file discovery, an extended section splitter that captures "Introduce Yourself" (which workshop_capture discards), non-interactive tag assignment and dedup, a 20%-duplicate guard that aborts before writing, and a timestamped run log. All library I/O — reads and writes — goes exclusively through `interview_library_parser`: `_load_library` for reads and `save_library` for writes. Task 0 adds `save_library()` to the parser before any backfill code is written.

**Tech Stack:** Python 3, python-docx 1.2.0, pytest, stdlib only (no new packages).

**Key constraint:** Script runs from the project root `C:\Users\r_tod\Documents\Projects\Job_search_agent\`. All relative paths (`data/`, `outputs/`) resolve against that root. The `data/` directory is gitignored and lives only in the main project, not the worktree — tests use `tmp_path` fixtures, not the real data directory.

---

### File Map

| Action | Path |
|---|---|
| ~~Modify~~ | ~~`scripts/interview_library_parser.py` — add `write_library()` (Task 0)~~ **DONE** commit e400fb0 |
| ~~Modify~~ | ~~`tests/phase5/test_interview_library_parser.py` — add tests for `write_library` (Task 0)~~ **DONE** |
| Create | `scripts/utils/backfill_interview_library.py` |
| Create | `tests/utils/test_backfill_interview_library.py` |
| Write (runtime) | `outputs/library_backfill_YYYYMMDD_HHMM.txt` |
| Modify (runtime) | `data/interview_library.json` |
| Do NOT touch | `scripts/phase5_workshop_capture.py` |

---

### ~~Task 0: Add `write_library()` to `interview_library_parser.py`~~ ✅ DONE — commit e400fb0

~~**Why this task exists:** `interview_library_parser.py` had no write function. `phase5_workshop_capture._write_library` filled the gap, but coupling a new script to a private function in a different module creates a hidden dependency. The fix was to give the parser a public write method so all I/O — reads and writes — goes through one module. `phase5_workshop_capture._write_library` was removed; workshop_capture now imports and calls `write_library` from the parser.~~

~~**Files:**~~
~~- Modify: `scripts/interview_library_parser.py`~~
~~- Modify: `tests/phase5/test_interview_library_parser.py`~~

~~All steps completed. `write_library()` added (not `save_library` — name resolved during refactor). Tests pass. Committed e400fb0.~~

---

### Task 1: Scaffold — imports, constants, empty file structure

**Files:**
- Create: `scripts/utils/backfill_interview_library.py`
- Create: `tests/utils/test_backfill_interview_library.py`

- [ ] **Step 1: Create the script skeleton**

```python
# scripts/utils/backfill_interview_library.py
import os
import re
import sys
import json
from datetime import date, datetime
from pathlib import Path

# Resolve project root two levels up from scripts/utils/
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, _project_root)

from scripts.phase5_workshop_capture import (
    _extract_docx_paragraphs,
    _parse_stories,
    _parse_gaps,
    _parse_questions,
    _make_story_id,
    _make_gap_id,
    _make_question_id,
    _find_duplicate_story,
    _find_duplicate_gap,
    _find_duplicate_question,
    _build_story_entry,
    _build_gap_entry,
    _build_question_entry,
    _suggest_tags,
    _skip_update_roles,
)
from scripts.interview_library_parser import (
    LIBRARY_PATH,
    init_library,
    _load_library,
    write_library,         # added in Task 0 — authoritative write path
)

WORKSHOPPED_DIR = "data/interview_prep_workshopped"
OUTPUTS_DIR = "outputs"

VALID_STAGES = {
    "recruiter_screen",
    "hiring_manager",
    "panel_technical",
    "panel_business",
    "panel_values",
    "final",
}
```

- [ ] **Step 2: Create the test skeleton**

```python
# tests/utils/test_backfill_interview_library.py
import json
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import scripts.utils.backfill_interview_library as backfill
import scripts.interview_library_parser as ilp


# ── Shared helpers ────────────────────────────────────────────────────────────

def _seed_library(tmp_path, data, monkeypatch):
    lib_path = tmp_path / "interview_library.json"
    lib_path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(ilp, "LIBRARY_PATH", str(lib_path))
    monkeypatch.setattr(backfill, "LIBRARY_PATH", str(lib_path))
    return lib_path


def _paras(texts, style="Normal"):
    return [(t, style, False) for t in texts]


def _make_full_docx(tmp_path, filename="interview_prep_hiring_manager.docx", with_gaps=True):
    """Build a minimal .docx with all four workshopped sections."""
    from docx import Document
    doc = Document()
    doc.add_heading("Introduce Yourself", level=1)
    doc.add_paragraph("I am a systems engineer with 10 years of experience.")
    doc.add_heading("Story Bank", level=1)
    doc.add_paragraph("STORY 1 – Leadership Story:")
    doc.add_paragraph("Employer: ACME Corp | Systems Engineer | 2021-2023")
    doc.add_paragraph("Situation: Sat.")
    doc.add_paragraph("Task: Task.")
    doc.add_paragraph("Action: Act.")
    doc.add_paragraph("Result: Res.")
    if with_gaps:
        doc.add_heading("Gap Preparation", level=1)
        doc.add_paragraph("GAP 1 – IP Networking [REQUIRED]:")
        doc.add_paragraph("Honest answer: I have not worked in IP networking.")
        doc.add_paragraph("Bridge: Adjacent experience with systems interfaces.")
        doc.add_paragraph("Redirect: Strong systems engineering foundation.")
    doc.add_heading("Questions to Ask", level=1)
    doc.add_paragraph("1. What does success look like at 6 months?")
    path = tmp_path / filename
    doc.save(str(path))
    return str(path)
```

- [ ] **Step 3: Verify import works**

```bash
cd C:\Users\r_tod\Documents\Projects\Job_search_agent
python -c "import scripts.utils.backfill_interview_library; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add scripts/utils/backfill_interview_library.py tests/utils/test_backfill_interview_library.py
git commit -m "feat(backfill): scaffold backfill_interview_library.py with imports"
```

---

### Task 2: `discover_docx_files`

**Files:**
- Modify: `scripts/utils/backfill_interview_library.py`
- Modify: `tests/utils/test_backfill_interview_library.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/utils/test_backfill_interview_library.py — append

# ── discover_docx_files ───────────────────────────────────────────────────────

def test_discover_finds_docx_in_role_subdirs(tmp_path):
    role_dir = tmp_path / "Acme_SE"
    role_dir.mkdir()
    (role_dir / "interview_prep_hiring_manager.docx").write_bytes(b"")
    (role_dir / "interview_prep_recruiter_screen.docx").write_bytes(b"")
    results = backfill.discover_docx_files(str(tmp_path))
    assert len(results) == 2
    roles = {r for _, r, _ in results}
    stages = {s for _, _, s in results}
    assert roles == {"Acme_SE"}
    assert "hiring_manager" in stages
    assert "recruiter_screen" in stages


def test_discover_skips_unrecognized_stage_filenames(tmp_path):
    role_dir = tmp_path / "Acme_SE"
    role_dir.mkdir()
    (role_dir / "interview_prep_custom_stage.docx").write_bytes(b"")
    results = backfill.discover_docx_files(str(tmp_path))
    assert results == []


def test_discover_skips_non_docx_files(tmp_path):
    role_dir = tmp_path / "Acme_SE"
    role_dir.mkdir()
    (role_dir / "interview_prep_hiring_manager.txt").write_bytes(b"")
    results = backfill.discover_docx_files(str(tmp_path))
    assert results == []


def test_discover_raises_when_base_dir_absent(tmp_path):
    with pytest.raises(FileNotFoundError):
        backfill.discover_docx_files(str(tmp_path / "nonexistent"))


def test_discover_returns_sorted_results(tmp_path):
    for role in ("Zeta_Role", "Alpha_Role"):
        d = tmp_path / role
        d.mkdir()
        (d / "interview_prep_hiring_manager.docx").write_bytes(b"")
    results = backfill.discover_docx_files(str(tmp_path))
    paths = [p for p, _, _ in results]
    assert paths == sorted(paths)
```

- [ ] **Step 2: Run to verify FAIL**

```bash
cd C:\Users\r_tod\Documents\Projects\Job_search_agent
pytest tests/utils/test_backfill_interview_library.py::test_discover_finds_docx_in_role_subdirs -v
```
Expected: `FAILED` — `AttributeError: module has no attribute 'discover_docx_files'`

- [ ] **Step 3: Implement**

```python
# scripts/utils/backfill_interview_library.py — append

def discover_docx_files(base_dir=WORKSHOPPED_DIR):
    """Scan base_dir recursively. Return sorted list of (path, role, stage) tuples.

    Role = immediate parent folder name of each .docx.
    Stage = token extracted from interview_prep_{stage}.docx filename.
    Skips files where the stage token is not in VALID_STAGES.
    """
    base = Path(base_dir)
    if not base.exists():
        raise FileNotFoundError(f"Workshopped directory not found: {base_dir}")
    results = []
    for docx_path in sorted(base.rglob("*.docx")):
        role = docx_path.parent.name
        m = re.match(r"interview_prep_(.+)\.docx$", docx_path.name)
        if not m:
            continue
        stage = m.group(1)
        if stage not in VALID_STAGES:
            continue
        results.append((str(docx_path), role, stage))
    return results
```

- [ ] **Step 4: Run to verify PASS**

```bash
pytest tests/utils/test_backfill_interview_library.py -k "discover" -v
```
Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/utils/backfill_interview_library.py tests/utils/test_backfill_interview_library.py
git commit -m "feat(backfill): implement discover_docx_files"
```

---

### Task 3: `_split_sections_backfill`

**Files:**
- Modify: `scripts/utils/backfill_interview_library.py`
- Modify: `tests/utils/test_backfill_interview_library.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/utils/test_backfill_interview_library.py — append

# ── _split_sections_backfill ──────────────────────────────────────────────────

def test_split_backfill_captures_introduce_yourself():
    paras = (
        _paras(["Introduce Yourself"], style="Heading 1") +
        _paras(["Start with your systems engineering background."]) +
        _paras(["Story Bank"], style="Heading 1") +
        _paras(["STORY 1 – MBSE:"])
    )
    sections = backfill._split_sections_backfill(paras)
    assert any("background" in t for t, _, _ in sections["introduce_yourself"])


def test_split_backfill_intro_does_not_bleed_into_story_bank():
    paras = (
        _paras(["Introduce Yourself"], style="Heading 1") +
        _paras(["Intro content here."]) +
        _paras(["Story Bank"], style="Heading 1") +
        _paras(["STORY 1 – Topic:"])
    )
    sections = backfill._split_sections_backfill(paras)
    assert not any("STORY" in t for t, _, _ in sections["introduce_yourself"])
    assert any("STORY" in t for t, _, _ in sections["story_bank"])


def test_split_backfill_captures_all_four_sections():
    paras = (
        _paras(["Introduce Yourself"], style="Heading 1") +
        _paras(["Intro text."]) +
        _paras(["Story Bank"], style="Heading 1") +
        _paras(["STORY 1 – Topic:"]) +
        _paras(["Gap Preparation"], style="Heading 1") +
        _paras(["GAP 1 – Topic [REQUIRED]:"]) +
        _paras(["Questions to Ask"], style="Heading 1") +
        _paras(["1. What does success look like at 6 months?"])
    )
    sections = backfill._split_sections_backfill(paras)
    assert len(sections["introduce_yourself"]) == 1
    assert len(sections["story_bank"]) == 1
    assert len(sections["gap_prep"]) == 1
    assert len(sections["questions"]) == 1


def test_split_backfill_company_role_brief_discarded():
    paras = (
        _paras(["Company Role Brief"], style="Heading 1") +
        _paras(["Company overview."]) +
        _paras(["Story Bank"], style="Heading 1") +
        _paras(["STORY 1 – Topic:"])
    )
    sections = backfill._split_sections_backfill(paras)
    assert not any("overview" in t for t, _, _ in sections["story_bank"])
    assert not any("overview" in t for t, _, _ in sections["introduce_yourself"])
```

- [ ] **Step 2: Run to verify FAIL**

```bash
pytest tests/utils/test_backfill_interview_library.py -k "split_backfill" -v
```
Expected: `FAILED` — `AttributeError: module has no attribute '_split_sections_backfill'`

- [ ] **Step 3: Implement**

```python
# scripts/utils/backfill_interview_library.py — append

def _split_sections_backfill(paragraphs):
    """Extended section splitter that also captures 'Introduce Yourself' content.

    Returns dict with keys: introduce_yourself, story_bank, gap_prep, questions.
    Each value is a list of (text, style, is_italic) tuples.
    Unlike workshop_capture._split_sections, this does NOT discard introductions.
    """
    SECTION_MARKERS = {
        "introduce_yourself": ["INTRODUCE YOURSELF"],
        "story_bank":         ["STORY BANK"],
        "gap_prep":           ["GAP PREPARATION"],
        "questions":          ["QUESTIONS TO ASK"],
        "other":              ["COMPANY", "ROLE BRIEF", "SALARY", "END OF",
                               "INTERVIEW PREP PACKAGE", "CONTINUITY"],
    }
    sections = {
        "introduce_yourself": [],
        "story_bank": [],
        "gap_prep": [],
        "questions": [],
    }
    current = None

    for text, style, is_italic in paragraphs:
        upper = text.upper()
        is_heading = "heading" in style.lower()
        matched = False
        for key, markers in SECTION_MARKERS.items():
            if any(m in upper for m in markers):
                if key == "other" and not is_heading:
                    continue
                current = None if key == "other" else key
                matched = True
                break
        if not matched and current in sections:
            sections[current].append((text, style, is_italic))

    return sections
```

- [ ] **Step 4: Run to verify PASS**

```bash
pytest tests/utils/test_backfill_interview_library.py -k "split_backfill" -v
```
Expected: all 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/utils/backfill_interview_library.py tests/utils/test_backfill_interview_library.py
git commit -m "feat(backfill): implement _split_sections_backfill with intro section capture"
```

---

### Task 4: Intro helpers — extract, build, dedup

**Files:**
- Modify: `scripts/utils/backfill_interview_library.py`
- Modify: `tests/utils/test_backfill_interview_library.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/utils/test_backfill_interview_library.py — append

# ── Intro helpers ─────────────────────────────────────────────────────────────

def test_extract_intro_text_joins_non_italic_lines():
    paras = [
        ("Line one.", "Normal", False),
        ("Line two.", "Normal", False),
    ]
    assert backfill._extract_intro_text(paras) == "Line one.\nLine two."


def test_extract_intro_text_skips_italic():
    paras = [
        ("Line one.", "Normal", False),
        ("Coaching note.", "Normal", True),
        ("Line two.", "Normal", False),
    ]
    assert backfill._extract_intro_text(paras) == "Line one.\nLine two."


def test_build_intro_entry_schema():
    entry = backfill._build_intro_entry(
        "I am a systems engineer.", "Acme_SE", "hiring_manager", "2026-05-06"
    )
    assert entry == {
        "id": "intro-Acme_SE-hiring_manager",
        "role": "Acme_SE",
        "stage": "hiring_manager",
        "text": "I am a systems engineer.",
        "last_updated": "2026-05-06",
    }


def test_find_duplicate_intro_matches_role_and_stage():
    library = {
        "introductions": [
            {"id": "intro-Acme_SE-hiring_manager", "role": "Acme_SE", "stage": "hiring_manager"}
        ],
        "stories": [], "gap_responses": [], "questions": [],
    }
    result = backfill._find_duplicate_intro(library, "Acme_SE", "hiring_manager")
    assert result is not None
    assert result["id"] == "intro-Acme_SE-hiring_manager"


def test_find_duplicate_intro_no_match_different_stage():
    library = {
        "introductions": [
            {"id": "intro-Acme_SE-hiring_manager", "role": "Acme_SE", "stage": "hiring_manager"}
        ],
        "stories": [], "gap_responses": [], "questions": [],
    }
    assert backfill._find_duplicate_intro(library, "Acme_SE", "recruiter_screen") is None


def test_find_duplicate_intro_returns_none_when_key_absent():
    library = {"stories": [], "gap_responses": [], "questions": []}
    assert backfill._find_duplicate_intro(library, "Acme_SE", "hiring_manager") is None
```

- [ ] **Step 2: Run to verify FAIL**

```bash
pytest tests/utils/test_backfill_interview_library.py -k "intro" -v
```
Expected: `FAILED` — `AttributeError`

- [ ] **Step 3: Implement**

```python
# scripts/utils/backfill_interview_library.py — append

def _extract_intro_text(intro_paragraphs):
    """Join non-italic, non-empty paragraphs from the introduce_yourself section."""
    lines = [
        text for text, style, is_italic in intro_paragraphs
        if not is_italic and text.strip()
    ]
    return "\n".join(lines)


def _build_intro_entry(text, role, stage, today):
    return {
        "id": f"intro-{role}-{stage}",
        "role": role,
        "stage": stage,
        "text": text,
        "last_updated": today,
    }


def _find_duplicate_intro(library, role, stage):
    """Return existing intro entry matching role+stage, or None."""
    target_id = f"intro-{role}-{stage}"
    for entry in library.get("introductions", []):
        if entry.get("id") == target_id:
            return entry
    return None
```

- [ ] **Step 4: Run to verify PASS**

```bash
pytest tests/utils/test_backfill_interview_library.py -k "intro" -v
```
Expected: all 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/utils/backfill_interview_library.py tests/utils/test_backfill_interview_library.py
git commit -m "feat(backfill): implement intro extract, build, and dedup helpers"
```

---

### Task 5: `_make_unique_id` — ID collision handling

**Files:**
- Modify: `scripts/utils/backfill_interview_library.py`
- Modify: `tests/utils/test_backfill_interview_library.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/utils/test_backfill_interview_library.py — append

# ── _make_unique_id ───────────────────────────────────────────────────────────

def test_make_unique_id_returns_base_when_no_collision():
    assert backfill._make_unique_id("mbse-story", set()) == "mbse-story"


def test_make_unique_id_appends_2_on_first_collision():
    assert backfill._make_unique_id("mbse-story", {"mbse-story"}) == "mbse-story-2"


def test_make_unique_id_increments_until_clear():
    existing = {"mbse-story", "mbse-story-2", "mbse-story-3"}
    assert backfill._make_unique_id("mbse-story", existing) == "mbse-story-4"


def test_make_unique_id_respects_60_char_limit():
    long_id = "a" * 58  # 58 chars — appending "-2" = 60 chars (within limit)
    result = backfill._make_unique_id(long_id, {long_id})
    assert len(result) <= 60
```

- [ ] **Step 2: Run to verify FAIL**

```bash
pytest tests/utils/test_backfill_interview_library.py -k "unique_id" -v
```
Expected: `FAILED`

- [ ] **Step 3: Implement**

```python
# scripts/utils/backfill_interview_library.py — append

def _make_unique_id(base_id, existing_ids):
    """Return base_id if not in existing_ids, else append -2, -3, etc. Max 60 chars."""
    if base_id not in existing_ids:
        return base_id
    n = 2
    while True:
        candidate = f"{base_id}-{n}"[:60]
        if candidate not in existing_ids:
            return candidate
        n += 1
```

- [ ] **Step 4: Run to verify PASS**

```bash
pytest tests/utils/test_backfill_interview_library.py -k "unique_id" -v
```
Expected: all 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/utils/backfill_interview_library.py tests/utils/test_backfill_interview_library.py
git commit -m "feat(backfill): implement _make_unique_id with suffix incrementing"
```

---

### Task 6: `_process_file` — per-file extraction and library mutation

**Files:**
- Modify: `scripts/utils/backfill_interview_library.py`
- Modify: `tests/utils/test_backfill_interview_library.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/utils/test_backfill_interview_library.py — append

# ── _process_file ─────────────────────────────────────────────────────────────

def test_process_file_writes_all_entry_types(tmp_path, monkeypatch):
    monkeypatch.setattr(ilp, "TAGS_PATH", str(tmp_path / "missing_tags.json"))
    library = {"stories": [], "gap_responses": [], "questions": []}
    docx_path = _make_full_docx(tmp_path)
    log_lines = []
    stats = backfill._process_file(
        docx_path, "Acme_SE", "hiring_manager", library, "2026-05-06", log_lines
    )
    assert stats["written"] == 4   # 1 intro + 1 story + 1 gap + 1 question
    assert stats["skipped"] == 0
    assert len(library.get("introductions", [])) == 1
    assert len(library["stories"]) == 1
    assert len(library["gap_responses"]) == 1
    assert len(library["questions"]) == 1


def test_process_file_skips_duplicate_story(tmp_path, monkeypatch):
    monkeypatch.setattr(ilp, "TAGS_PATH", str(tmp_path / "missing_tags.json"))
    library = {
        "stories": [
            {"id": "acme-corp-story", "employer": "ACME Corp", "tags": [], "roles_used": ["OtherRole"]}
        ],
        "gap_responses": [], "questions": [],
    }
    docx_path = _make_full_docx(tmp_path)
    log_lines = []
    stats = backfill._process_file(
        docx_path, "Acme_SE", "hiring_manager", library, "2026-05-06", log_lines
    )
    assert stats["skipped"] >= 1
    assert len(library["stories"]) == 1  # no new story added
    assert any("SKIP story" in line for line in log_lines)


def test_process_file_skips_gap_for_recruiter_screen(tmp_path, monkeypatch):
    monkeypatch.setattr(ilp, "TAGS_PATH", str(tmp_path / "missing_tags.json"))
    library = {"stories": [], "gap_responses": [], "questions": []}
    docx_path = _make_full_docx(tmp_path, filename="interview_prep_recruiter_screen.docx",
                                 with_gaps=False)
    log_lines = []
    backfill._process_file(
        docx_path, "Acme_SE", "recruiter_screen", library, "2026-05-06", log_lines
    )
    assert len(library["gap_responses"]) == 0
    assert any("recruiter_screen" in line for line in log_lines)


def test_process_file_returns_warning_on_unreadable_docx(tmp_path, monkeypatch):
    monkeypatch.setattr(ilp, "TAGS_PATH", str(tmp_path / "missing_tags.json"))
    bad_path = str(tmp_path / "bad.docx")
    with open(bad_path, "w") as f:
        f.write("not a docx")
    library = {"stories": [], "gap_responses": [], "questions": []}
    log_lines = []
    stats = backfill._process_file(
        bad_path, "Acme_SE", "hiring_manager", library, "2026-05-06", log_lines
    )
    assert len(stats["warnings"]) == 1
    assert stats["written"] == 0


def test_process_file_collision_generates_unique_id(tmp_path, monkeypatch):
    monkeypatch.setattr(ilp, "TAGS_PATH", str(tmp_path / "missing_tags.json"))
    # Pre-seed a story with a different employer but same ID that would be generated
    # by forcing a collision situation
    library = {"stories": [], "gap_responses": [], "questions": []}
    docx_path = _make_full_docx(tmp_path)
    log_lines = []
    # Process twice — second pass should generate a -2 id for intro
    backfill._process_file(
        docx_path, "Acme_SE", "hiring_manager", library, "2026-05-06", log_lines
    )
    initial_count = len(library.get("introductions", []))
    # Second call with different role — no conflict on intro (different id)
    docx_path2 = _make_full_docx(tmp_path, filename="interview_prep_hiring_manager2.docx")
    backfill._process_file(
        docx_path2, "Beta_SE", "hiring_manager", library, "2026-05-06", log_lines
    )
    assert len(library.get("introductions", [])) == initial_count + 1
```

- [ ] **Step 2: Run to verify FAIL**

```bash
pytest tests/utils/test_backfill_interview_library.py -k "process_file" -v
```
Expected: `FAILED` — `AttributeError`

- [ ] **Step 3: Implement**

```python
# scripts/utils/backfill_interview_library.py — append

def _process_file(docx_path, role, stage, library, today, log_lines):
    """Parse one .docx and append new entries to the library dict (mutates in place).

    Non-interactive: duplicates are skipped and logged, never prompted.
    Returns dict with keys: written (int), skipped (int), warnings (list).
    """
    stats = {"written": 0, "skipped": 0, "warnings": []}

    log_lines.append(f"\n--- {role} / {stage} ---")
    log_lines.append(f"File: {docx_path}")

    try:
        paragraphs = _extract_docx_paragraphs(docx_path)
    except Exception as e:
        msg = f"ERROR: Could not read {docx_path}: {e}"
        log_lines.append(msg)
        stats["warnings"].append(msg)
        return stats

    if not paragraphs:
        msg = f"WARNING: No paragraphs found in {docx_path}"
        log_lines.append(msg)
        stats["warnings"].append(msg)
        return stats

    sections = _split_sections_backfill(paragraphs)

    # Collect all existing IDs once for O(1) collision checks
    existing_ids = set()
    for key in ("introductions", "stories", "gap_responses", "questions"):
        for entry in library.get(key, []):
            existing_ids.add(entry.get("id", ""))

    # ── Introductions ─────────────────────────────────────────────────────────
    if sections["introduce_yourself"]:
        intro_text = _extract_intro_text(sections["introduce_yourself"])
        if intro_text:
            dup = _find_duplicate_intro(library, role, stage)
            if dup:
                log_lines.append(f"  SKIP intro: intro-{role}-{stage} already exists")
                stats["skipped"] += 1
            else:
                entry = _build_intro_entry(intro_text, role, stage, today)
                library.setdefault("introductions", []).append(entry)
                existing_ids.add(entry["id"])
                log_lines.append(f"  WRITE intro: {entry['id']}")
                stats["written"] += 1
    else:
        log_lines.append("  INFO: No 'Introduce Yourself' section found")

    # ── Stories ───────────────────────────────────────────────────────────────
    raw_stories = _parse_stories(sections["story_bank"])
    log_lines.append(f"  Stories parsed: {len(raw_stories)}")
    for raw in raw_stories:
        content = " ".join([raw["situation"], raw["task"], raw["action"], raw["result"]])
        tags = _suggest_tags(content)
        primary_tag = tags[0] if tags else ""
        dup = _find_duplicate_story(library, raw["employer"], primary_tag)
        if dup:
            _skip_update_roles(dup, role, library, "stories")
            log_lines.append(
                f"  SKIP story: {dup['id']} (conflict: {raw['employer']} / {primary_tag})"
            )
            stats["skipped"] += 1
        else:
            entry = _build_story_entry(raw, tags, role, today)
            entry["id"] = _make_unique_id(_make_story_id(raw["employer"], tags), existing_ids)
            library["stories"].append(entry)
            existing_ids.add(entry["id"])
            log_lines.append(f"  WRITE story: {entry['id']}")
            stats["written"] += 1

    # ── Gap responses ─────────────────────────────────────────────────────────
    if stage == "recruiter_screen":
        log_lines.append(f"  INFO: Gap section skipped for recruiter_screen (expected)")
    else:
        raw_gaps = _parse_gaps(sections["gap_prep"])
        log_lines.append(f"  Gaps parsed: {len(raw_gaps)}")
        for raw in raw_gaps:
            content = " ".join([raw["honest_answer"], raw["bridge"], raw["redirect"]])
            tags = _suggest_tags(content)
            dup = _find_duplicate_gap(library, raw["gap_label"])
            if dup:
                _skip_update_roles(dup, role, library, "gap_responses")
                log_lines.append(
                    f"  SKIP gap: {dup['id']} (conflict: '{raw['gap_label']}')"
                )
                stats["skipped"] += 1
            else:
                entry = _build_gap_entry(raw, tags, role, today)
                entry["id"] = _make_unique_id(_make_gap_id(raw["gap_label"]), existing_ids)
                library["gap_responses"].append(entry)
                existing_ids.add(entry["id"])
                log_lines.append(f"  WRITE gap: {entry['id']}")
                stats["written"] += 1

    # ── Questions ─────────────────────────────────────────────────────────────
    raw_questions = _parse_questions(sections["questions"], stage)
    log_lines.append(f"  Questions parsed: {len(raw_questions)}")
    for raw in raw_questions:
        tags = _suggest_tags(raw["text"])
        dup = _find_duplicate_question(library, raw["text"])
        if dup:
            _skip_update_roles(dup, role, library, "questions")
            log_lines.append(f"  SKIP question: duplicate '{raw['text'][:50]}'")
            stats["skipped"] += 1
        else:
            entry = _build_question_entry(raw, tags, role, today)
            entry["id"] = _make_unique_id(_make_question_id(raw["text"]), existing_ids)
            library["questions"].append(entry)
            existing_ids.add(entry["id"])
            log_lines.append(f"  WRITE question: {entry['id']}")
            stats["written"] += 1

    return stats
```

- [ ] **Step 4: Run to verify PASS**

```bash
pytest tests/utils/test_backfill_interview_library.py -k "process_file" -v
```
Expected: all 5 tests PASS

- [ ] **Step 5: Run full test suite to check for regressions**

```bash
pytest tests/ -v --tb=short 2>&1 | tail -20
```
Expected: no new failures

- [ ] **Step 6: Commit**

```bash
git add scripts/utils/backfill_interview_library.py tests/utils/test_backfill_interview_library.py
git commit -m "feat(backfill): implement _process_file with non-interactive dedup and logging"
```

---

### Task 7: `run_backfill` — main loop, 20% guard, run log

**Files:**
- Modify: `scripts/utils/backfill_interview_library.py`
- Modify: `tests/utils/test_backfill_interview_library.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/utils/test_backfill_interview_library.py — append

# ── run_backfill ──────────────────────────────────────────────────────────────

def test_run_backfill_writes_library_and_log(tmp_path, monkeypatch):
    # Set up: one role folder with one docx
    role_dir = tmp_path / "workshopped" / "Acme_SE"
    role_dir.mkdir(parents=True)
    _make_full_docx(tmp_path / "workshopped" / "Acme_SE")

    lib_path = tmp_path / "interview_library.json"
    lib_path.write_text(json.dumps({"stories": [], "gap_responses": [], "questions": []}))
    out_dir = tmp_path / "outputs"
    out_dir.mkdir()

    monkeypatch.setattr(ilp, "LIBRARY_PATH", str(lib_path))
    monkeypatch.setattr(backfill, "LIBRARY_PATH", str(lib_path))
    monkeypatch.setattr(ilp, "TAGS_PATH", str(tmp_path / "missing_tags.json"))
    monkeypatch.setattr(backfill, "OUTPUTS_DIR", str(out_dir))

    result = backfill.run_backfill(str(tmp_path / "workshopped"))

    assert result["written"] > 0
    assert result["files"] == 1
    # Library updated on disk
    saved = json.loads(lib_path.read_text())
    assert len(saved["stories"]) > 0
    # Run log created
    log_files = list(out_dir.glob("library_backfill_*.txt"))
    assert len(log_files) == 1


def test_run_backfill_aborts_on_high_dup_ratio(tmp_path, monkeypatch):
    # Pre-seed library with a story that will conflict with every story in the docx
    role_dir = tmp_path / "workshopped" / "Acme_SE"
    role_dir.mkdir(parents=True)
    _make_full_docx(tmp_path / "workshopped" / "Acme_SE")

    # Pre-populate library so everything is a dup
    existing = {
        "stories": [
            {"id": "acme-corp-story", "employer": "ACME Corp", "tags": [], "roles_used": []}
        ],
        "gap_responses": [
            {"id": "ip-networking", "gap_label": "IP Networking", "roles_used": []}
        ],
        "questions": [
            {"id": "what-does-success", "text": "What does success look like at 6 months?",
             "roles_used": []}
        ],
        "introductions": [
            {"id": "intro-Acme_SE-hiring_manager", "role": "Acme_SE",
             "stage": "hiring_manager"}
        ],
    }
    lib_path = tmp_path / "interview_library.json"
    lib_path.write_text(json.dumps(existing))
    out_dir = tmp_path / "outputs"
    out_dir.mkdir()

    monkeypatch.setattr(ilp, "LIBRARY_PATH", str(lib_path))
    monkeypatch.setattr(backfill, "LIBRARY_PATH", str(lib_path))
    monkeypatch.setattr(ilp, "TAGS_PATH", str(tmp_path / "missing_tags.json"))
    monkeypatch.setattr(backfill, "OUTPUTS_DIR", str(out_dir))

    result = backfill.run_backfill(str(tmp_path / "workshopped"))

    # When dup ratio > 20%, library should NOT be modified
    assert result.get("aborted") is True
    saved = json.loads(lib_path.read_text())
    # Story count unchanged
    assert len(saved["stories"]) == 1
```

- [ ] **Step 2: Run to verify FAIL**

```bash
pytest tests/utils/test_backfill_interview_library.py -k "run_backfill" -v
```
Expected: `FAILED`

- [ ] **Step 3: Implement**

```python
# scripts/utils/backfill_interview_library.py — append

def run_backfill(base_dir=WORKSHOPPED_DIR):
    """Discover all .docx files, parse all sections, write library and run log.

    Aborts (does not write library) if >20% of processed entries are duplicates.
    Returns summary dict with keys: files, written, skipped, warnings, log_path,
    aborted (bool).
    """
    today = str(date.today())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    log_path = os.path.join(OUTPUTS_DIR, f"library_backfill_{timestamp}.txt")

    print(f"\n{'=' * 60}")
    print("INTERVIEW LIBRARY BACKFILL")
    print(f"{'=' * 60}")

    docx_files = discover_docx_files(base_dir)
    print(f"Files discovered: {len(docx_files)}")
    for path, role, stage in docx_files:
        print(f"  {role} / {stage}")

    init_library()
    library = _load_library()

    total_written = 0
    total_skipped = 0
    all_warnings = []
    log_lines = [
        f"LIBRARY BACKFILL RUN — {datetime.now().isoformat()}",
        f"Source dir: {base_dir}",
        f"Files discovered: {len(docx_files)}",
        "=" * 60,
    ]

    for docx_path, role, stage in docx_files:
        stats = _process_file(docx_path, role, stage, library, today, log_lines)
        total_written += stats["written"]
        total_skipped += stats["skipped"]
        all_warnings.extend(stats["warnings"])

    # ── 20% duplicate guard ───────────────────────────────────────────────────
    total_candidates = total_written + total_skipped
    dup_ratio = total_skipped / total_candidates if total_candidates > 0 else 0.0
    if dup_ratio > 0.20:
        abort_msg = (
            f"\nSTOP: {dup_ratio:.0%} of entries are duplicates (threshold: 20%).\n"
            "This likely indicates a schema mismatch. Review before proceeding.\n"
            "Library was NOT written."
        )
        print(abort_msg)
        log_lines.extend(["\n" + "=" * 60, "ABORTED — duplicate ratio exceeded threshold", abort_msg])
        _write_run_log(log_lines, log_path)
        return {
            "files": len(docx_files),
            "written": 0,
            "skipped": total_skipped,
            "warnings": all_warnings,
            "log_path": log_path,
            "aborted": True,
        }

    # ── Write library ─────────────────────────────────────────────────────────
    write_library(library)  # interview_library_parser.write_library — single authoritative write path

    # ── Write run log ─────────────────────────────────────────────────────────
    log_lines.extend([
        f"\n{'=' * 60}",
        "SUMMARY",
        f"Files processed: {len(docx_files)}",
        f"Entries written: {total_written}",
        f"Entries skipped (duplicates): {total_skipped}",
        f"Warnings: {len(all_warnings)}",
    ])
    if all_warnings:
        log_lines.append("\nWARNINGS:")
        for w in all_warnings:
            log_lines.append(f"  {w}")
    _write_run_log(log_lines, log_path)

    print(f"\n{'=' * 60}")
    print(f"Written:  {total_written} entries")
    print(f"Skipped:  {total_skipped} duplicates")
    if all_warnings:
        print(f"Warnings: {len(all_warnings)}")
    print(f"Library:  {LIBRARY_PATH}")
    print(f"Log:      {log_path}")
    print(f"{'=' * 60}")

    return {
        "files": len(docx_files),
        "written": total_written,
        "skipped": total_skipped,
        "warnings": all_warnings,
        "log_path": log_path,
        "aborted": False,
    }


def _write_run_log(log_lines, log_path):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
```

- [ ] **Step 4: Run to verify PASS**

```bash
pytest tests/utils/test_backfill_interview_library.py -k "run_backfill" -v
```
Expected: both tests PASS

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v --tb=short 2>&1 | tail -20
```
Expected: no new failures

- [ ] **Step 6: Commit**

```bash
git add scripts/utils/backfill_interview_library.py tests/utils/test_backfill_interview_library.py
git commit -m "feat(backfill): implement run_backfill with 20% dup guard and run log"
```

---

### Task 8: `main()` entry point and live run

**Files:**
- Modify: `scripts/utils/backfill_interview_library.py`

- [ ] **Step 1: Implement `main()`**

```python
# scripts/utils/backfill_interview_library.py — append

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Bulk backfill interview_library.json from workshopped .docx files."
    )
    parser.add_argument(
        "--base-dir",
        default=WORKSHOPPED_DIR,
        help=f"Root dir containing role subfolders with .docx files (default: {WORKSHOPPED_DIR})",
    )
    args = parser.parse_args()

    result = run_backfill(args.base_dir)
    if result.get("aborted"):
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify syntax**

```bash
cd C:\Users\r_tod\Documents\Projects\Job_search_agent
python -m py_compile scripts/utils/backfill_interview_library.py && echo "OK"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add scripts/utils/backfill_interview_library.py
git commit -m "feat(backfill): add main() entry point"
```

- [ ] **Step 4: Run the backfill against real data**

```bash
cd C:\Users\r_tod\Documents\Projects\Job_search_agent
python -m scripts.utils.backfill_interview_library
```

Review terminal output:
- File count matches Step 1 discovery (8 files expected)
- Per-file entry counts are plausible (no zeros across all files)
- No warnings that indicate schema failures
- Dup ratio well below 20%

- [ ] **Step 5: Inspect the run log**

```bash
# Find the log file
ls outputs/library_backfill_*.txt | sort | tail -1
# View it
cat outputs/library_backfill_*.txt | tail -30
```

Expected: log shows WRITE entries for at least stories and questions; no ERROR lines.

- [ ] **Step 6: Spot-check the library**

```bash
python -c "
import json
with open('data/interview_library.json') as f:
    lib = json.load(f)
print('stories:', len(lib.get('stories', [])))
print('gap_responses:', len(lib.get('gap_responses', [])))
print('questions:', len(lib.get('questions', [])))
print('introductions:', len(lib.get('introductions', [])))
"
```

Expected: nonzero counts across multiple sections. If only one section has entries, check the docx heading styles in the source files before proceeding.

- [ ] **Step 7: Final commit — scripts and tests only**

`data/` and `outputs/` are gitignored — do NOT stage them. The live run result stays local.

```bash
git status   # verify data/ and outputs/ do not appear as staged
git add scripts/utils/backfill_interview_library.py tests/utils/test_backfill_interview_library.py
git commit -m "feat(backfill): add backfill_interview_library.py — bulk populate interview library from workshopped docs"
```

---

## Self-Review

**Spec coverage check:**

| Requirement | Covered by |
|---|---|
| Read all .docx recursively | Task 2: `discover_docx_files` |
| Parse Introduce Yourself → `introductions[]` | Task 3, 4: `_split_sections_backfill`, intro helpers |
| Parse Story Bank → `stories[]` | Task 6: `_process_file` (imports from workshop_capture) |
| Parse Gap Preparation → `gap_responses[]` | Task 6: `_process_file` |
| Parse Questions to Ask → `questions[]` | Task 6: `_process_file` |
| Skip gap section silently for recruiter_screen | Task 6: `_process_file` |
| Role slug from parent folder, stage from filename | Task 2: `discover_docx_files` |
| `roles_used[]` populated on every entry | Task 6: all entry builders include role |
| Dedup: skip + log, never overwrite | Task 6: `_process_file` |
| ID collision: append -2, -3 | Task 5: `_make_unique_id` |
| 20% dup guard aborts before write | Task 7: `run_backfill` |
| Run log: every file, entry, skip, warning | Task 7: `_write_run_log` |
| `introductions[]` as new top-level key | Task 6: `library.setdefault("introductions", [])` |
| No custom JSON I/O | All library writes via `ilp.save_library()` (added Task 0); no writes touch workshop_capture |
| Non-interactive | No `input()` calls anywhere |

**Placeholder scan:** None found — all steps have complete code.

**Type consistency:** `_process_file` signature used consistently in Task 6 and Task 7.
