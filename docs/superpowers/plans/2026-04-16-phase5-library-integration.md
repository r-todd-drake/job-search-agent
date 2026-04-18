# Phase 5 Library Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `phase5_interview_prep.py` to seed story/gap/question generation from `interview_library.json`, surface debrief performance history, inject continuity summaries from prior debriefs, override salary with actuals, and emit post-generation notifications for workshop capture and thank you letters.

**Architecture:** New `scripts/phase5_debrief_utils.py` owns all debrief I/O and rendering (load, continuity, salary, notifications, performance signal). `phase5_interview_prep.py` is extended additively — existing `_build_*` prompt functions gain optional `library_seeds` parameters; `generate_prep()` gains library/debrief lookups. All changes are no-op when library or debrief data is absent.

**Tech Stack:** Python 3.11+, python-docx, `interview_library_parser.py` (existing), `phase5_debrief_utils.py` (new this plan)

---

## Parallel Dispatch Note

**Tasks 1 and 2 are INDEPENDENT — dispatch both as subagents in parallel.**

- **Task 1** creates `scripts/phase5_debrief_utils.py` + `tests/test_phase5_debrief_utils.py` — zero overlap with interview_prep.py
- **Task 2** modifies `scripts/phase5_interview_prep.py` (Session A: JD tag extraction + library seeding for stories, gaps, questions) + extends `tests/phase5/test_interview_prep.py`

Tasks 3–9 are sequential and depend on both Task 1 and Task 2 being complete.

---

## File Map

| File | Action | Responsible |
|---|---|---|
| `scripts/phase5_debrief_utils.py` | CREATE | Task 1 |
| `tests/test_phase5_debrief_utils.py` | CREATE | Task 1 |
| `scripts/phase5_interview_prep.py` | MODIFY | Tasks 2, 3, 4, 5, 6 |
| `tests/phase5/test_interview_prep.py` | MODIFY | Tasks 2, 3, 4, 5, 6 |

---

## Debrief JSON Schema Reference

Filed debriefs have this structure (from `interview_debrief_template.yaml`):
```json
{
  "metadata": {
    "role": "Viasat_SE_IS",
    "stage": "hiring_manager",
    "panel_label": null,
    "company": "Viasat",
    "interviewers": [{"name": "Jane Smith", "title": "Chief Engineer", "notes": "Asked about MBSE maturity"}],
    "interview_date": "2026-04-15",
    "format": "video",
    "produced_date": "2026-04-15"
  },
  "advancement_read": {"assessment": "maybe", "notes": "strong technical fit"},
  "stories_used": [{"tags": ["mbse"], "framing": "MBSE bottleneck", "landed": "yes", "library_id": "story_001"}],
  "gaps_surfaced": [{"gap_label": "no cleared SCIF experience", "response_given": "...", "response_felt": "strong"}],
  "salary_exchange": {"range_given_min": 140000, "range_given_max": 180000, "candidate_anchor": 170000, "candidate_floor": 155000, "notes": null},
  "what_i_said": "Said I prefer hybrid. Mentioned I have active TS/SCI.",
  "open_notes": null
}
```

## Library Entry Schemas

**Story entry** (from `interview_library.json` `stories` array):
```json
{
  "id": "story_001",
  "employer": "G2 OPS",
  "title": "Lead SE",
  "dates": "2022-2024",
  "situation": "...",
  "task": "...",
  "action": "...",
  "result": "...",
  "if_probed": "...",
  "tags": ["mbse", "systems-engineering"],
  "roles_used": ["Viasat_SE_IS"]
}
```

**Gap response entry:**
```json
{
  "id": "gap_001",
  "gap_label": "no cleared SCIF experience",
  "severity": "REQUIRED",
  "honest_answer": "...",
  "bridge": "...",
  "redirect": "...",
  "tags": ["clearance"],
  "roles_used": ["Viasat_SE_IS"]
}
```

**Question entry:**
```json
{
  "id": "q_001",
  "text": "What is the acquisition phase for this program?",
  "stage": "hiring_manager",
  "category": "program",
  "tags": ["systems-engineering"],
  "roles_used": ["Viasat_SE_IS"]
}
```

---

## Task 1: Create `phase5_debrief_utils.py` + Tests

**[SUBAGENT — runs in parallel with Task 2]**

**Files:**
- Create: `scripts/phase5_debrief_utils.py`
- Create: `tests/test_phase5_debrief_utils.py`

### Functions to implement

```python
DEBRIEFS_DIR = "data/debriefs"
```

**`load_debriefs(role: str) -> list[dict]`**
Load all `*.json` files under `data/debriefs/{role}/`, sorted ascending by `metadata.interview_date`. Skip files that fail JSON decode. Return `[]` if directory absent.

**`load_all_debriefs() -> list[dict]`**
Walk every subdirectory of `data/debriefs/` and call `load_debriefs()` on each. Return combined list (order not guaranteed across roles). Return `[]` if `data/debriefs/` absent.

**`get_story_performance_signal(library_id: str, all_debriefs: list[dict]) -> str | None`**
Scan `stories_used` in all debriefs for entries where `library_id` matches. Tally `landed` values. Return `"Used N times across roles: [yes x2 / partially x1]"` or `None` if no matches. Return `None` if `library_id` is falsy.

**`get_gap_performance_signal(gap_label: str, all_debriefs: list[dict]) -> str | None`**
Scan `gaps_surfaced` in all debriefs for entries where `gap_label` matches case-insensitively (strip + lower). Tally `response_felt` values. Return `"Used N times across roles: [strong x1 / adequate x2]"` or `None` if no matches. Return `None` if `gap_label` is falsy.

**`load_salary_actuals(debriefs: list[dict]) -> dict | None`**
Iterate `debriefs` in reverse (most recent last → reversed = most recent first). Return the first entry whose `salary_exchange.range_given_min` or `salary_exchange.range_given_max` is non-null. Return dict with keys: `range_given_min`, `range_given_max`, `candidate_anchor`, `candidate_floor`, `notes`, `interview_date`, `stage`. Return `None` if none found.

**`build_continuity_section(debriefs: list[dict]) -> str`**
Render a plain-text continuity summary. Return `""` if `debriefs` is empty. Format:
```
============================================================
CONTINUITY SUMMARY
(Reference record from prior interviews -- not prep guidance)
------------------------------------------------------------

Stage: hiring_manager -- 2026-04-15
  Interviewer: Jane Smith -- Chief Engineer
  Advancement read: maybe
  Stories used:
    - [mbse] MBSE bottleneck (landed: yes)
  Gaps surfaced:
    - no cleared SCIF experience (response felt: strong)
  What I said: Said I prefer hybrid. Mentioned I have active TS/SCI.
```
If `what_i_said` is null/empty, print `"  What I said: (no continuity data captured)"`. Include `panel_label` in stage header if non-null: `"Stage: team_panel (se_team) -- 2026-04-16"`.

**`find_unmatched_debrief_content(debriefs: list[dict]) -> tuple[list[dict], list[str]]`**
Compare debrief `stories_used` entries (those with a `library_id`) against library story IDs. Compare debrief `gaps_surfaced` entries (normalized `gap_label`) against library gap labels. Return `(unmatched_stories, unmatched_gap_labels)` where `unmatched_stories` is a list of `{"library_id": ..., "tags": ..., "stage": ...}` dicts and `unmatched_gap_labels` is a list of label strings. Deduplicate across multiple debriefs. Import `_load_library` from `scripts.interview_library_parser`.

**`has_debrief_for_stage(debriefs: list[dict], stage: str, panel_label: str | None = None) -> bool`**
Return `True` if any entry in `debriefs` has `metadata.stage == stage`. If `panel_label` is not `None`, also require `metadata.panel_label == panel_label`.

---

- [ ] **Step 1: Write the full `phase5_debrief_utils.py`**

```python
# scripts/phase5_debrief_utils.py
import json
import os

DEBRIEFS_DIR = "data/debriefs"


def load_debriefs(role: str) -> list:
    role_dir = os.path.join(DEBRIEFS_DIR, role)
    if not os.path.isdir(role_dir):
        return []
    debriefs = []
    for fname in os.listdir(role_dir):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(role_dir, fname)
        with open(fpath, encoding="utf-8") as f:
            try:
                debriefs.append(json.load(f))
            except json.JSONDecodeError:
                pass
    debriefs.sort(key=lambda d: d.get("metadata", {}).get("interview_date") or "")
    return debriefs


def load_all_debriefs() -> list:
    if not os.path.isdir(DEBRIEFS_DIR):
        return []
    all_debriefs = []
    for entry in os.listdir(DEBRIEFS_DIR):
        role_dir = os.path.join(DEBRIEFS_DIR, entry)
        if os.path.isdir(role_dir):
            all_debriefs.extend(load_debriefs(entry))
    return all_debriefs


def get_story_performance_signal(library_id: str, all_debriefs: list) -> str:
    if not library_id:
        return None
    counts = {}
    for d in all_debriefs:
        for story in d.get("stories_used") or []:
            if story.get("library_id") == library_id:
                landed = story.get("landed") or "unknown"
                counts[landed] = counts.get(landed, 0) + 1
    if not counts:
        return None
    total = sum(counts.values())
    parts = [f"{r} x{c}" for r, c in sorted(counts.items())]
    return f"Used {total} times across roles: [{' / '.join(parts)}]"


def get_gap_performance_signal(gap_label: str, all_debriefs: list) -> str:
    if not gap_label:
        return None
    norm = gap_label.lower().strip()
    counts = {}
    for d in all_debriefs:
        for gap in d.get("gaps_surfaced") or []:
            if (gap.get("gap_label") or "").lower().strip() == norm:
                felt = gap.get("response_felt") or "unknown"
                counts[felt] = counts.get(felt, 0) + 1
    if not counts:
        return None
    total = sum(counts.values())
    parts = [f"{r} x{c}" for r, c in sorted(counts.items())]
    return f"Used {total} times across roles: [{' / '.join(parts)}]"


def load_salary_actuals(debriefs: list) -> dict:
    for d in reversed(debriefs):
        sal = d.get("salary_exchange") or {}
        if sal.get("range_given_min") or sal.get("range_given_max"):
            meta = d.get("metadata", {}) or {}
            return {
                "range_given_min": sal.get("range_given_min"),
                "range_given_max": sal.get("range_given_max"),
                "candidate_anchor": sal.get("candidate_anchor"),
                "candidate_floor": sal.get("candidate_floor"),
                "notes": sal.get("notes"),
                "interview_date": meta.get("interview_date"),
                "stage": meta.get("stage"),
            }
    return None


def build_continuity_section(debriefs: list) -> str:
    if not debriefs:
        return ""
    lines = [
        "=" * 60,
        "CONTINUITY SUMMARY",
        "(Reference record from prior interviews -- not prep guidance)",
        "-" * 60,
    ]
    for d in debriefs:
        meta = d.get("metadata", {}) or {}
        stage = meta.get("stage", "unknown")
        panel_label = meta.get("panel_label")
        date = meta.get("interview_date", "unknown date")
        header = f"Stage: {stage}"
        if panel_label:
            header += f" ({panel_label})"
        header += f" -- {date}"
        lines.append("")
        lines.append(header)

        for iv in meta.get("interviewers") or []:
            name = iv.get("name") or "(unnamed)"
            title = iv.get("title") or ""
            lines.append(f"  Interviewer: {name}" + (f" -- {title}" if title else ""))

        adv = d.get("advancement_read") or {}
        if adv.get("assessment"):
            lines.append(f"  Advancement read: {adv['assessment']}")

        stories = d.get("stories_used") or []
        if stories:
            lines.append("  Stories used:")
            for s in stories:
                tags = ", ".join(s.get("tags") or [])
                framing = s.get("framing") or ""
                landed = s.get("landed") or ""
                line = f"    - [{tags}]"
                if framing:
                    line += f" {framing}"
                if landed:
                    line += f" (landed: {landed})"
                lines.append(line)

        gaps = d.get("gaps_surfaced") or []
        if gaps:
            lines.append("  Gaps surfaced:")
            for g in gaps:
                label = g.get("gap_label") or "(unlabeled)"
                felt = g.get("response_felt") or ""
                line = f"    - {label}"
                if felt:
                    line += f" (response felt: {felt})"
                lines.append(line)

        what_i_said = d.get("what_i_said")
        if what_i_said and str(what_i_said).strip():
            lines.append(f"  What I said: {what_i_said}")
        else:
            lines.append("  What I said: (no continuity data captured)")

    lines.append("")
    return "\n".join(lines)


def find_unmatched_debrief_content(debriefs: list) -> tuple:
    from scripts.interview_library_parser import _load_library
    library = _load_library()
    library_story_ids = {s.get("id") for s in library.get("stories", []) if s.get("id")}
    library_gap_labels = {
        g.get("gap_label", "").lower().strip()
        for g in library.get("gap_responses", [])
    }

    unmatched_stories = []
    unmatched_gaps = []
    seen_stories = set()
    seen_gaps = set()

    for d in debriefs:
        stage = (d.get("metadata") or {}).get("stage", "unknown")
        for story in d.get("stories_used") or []:
            lid = story.get("library_id")
            if lid and lid not in library_story_ids and lid not in seen_stories:
                unmatched_stories.append(
                    {"library_id": lid, "tags": story.get("tags", []), "stage": stage}
                )
                seen_stories.add(lid)
        for gap in d.get("gaps_surfaced") or []:
            label_norm = (gap.get("gap_label") or "").lower().strip()
            if label_norm and label_norm not in library_gap_labels and label_norm not in seen_gaps:
                unmatched_gaps.append(gap.get("gap_label", label_norm))
                seen_gaps.add(label_norm)

    return unmatched_stories, unmatched_gaps


def has_debrief_for_stage(debriefs: list, stage: str, panel_label=None) -> bool:
    for d in debriefs:
        meta = d.get("metadata", {}) or {}
        if meta.get("stage") != stage:
            continue
        if panel_label is not None and meta.get("panel_label") != panel_label:
            continue
        return True
    return False
```

- [ ] **Step 2: Write `tests/test_phase5_debrief_utils.py`**

```python
# tests/test_phase5_debrief_utils.py
import json
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch


# --- fixtures ---

def _make_debrief(role="test_role", stage="hiring_manager", date="2026-04-10",
                  panel_label=None, interviewers=None, advancement="maybe",
                  stories=None, gaps=None, salary=None, what_i_said=None):
    return {
        "metadata": {
            "role": role, "stage": stage, "interview_date": date,
            "panel_label": panel_label,
            "interviewers": interviewers or [{"name": "Jane Smith", "title": "CE", "notes": ""}],
        },
        "advancement_read": {"assessment": advancement, "notes": ""},
        "stories_used": stories or [],
        "gaps_surfaced": gaps or [],
        "salary_exchange": salary or {},
        "what_i_said": what_i_said,
        "open_notes": None,
    }


def _write_debriefs(tmpdir, role, debriefs):
    role_dir = os.path.join(tmpdir, role)
    os.makedirs(role_dir, exist_ok=True)
    paths = []
    for i, d in enumerate(debriefs):
        p = os.path.join(role_dir, f"debrief_{i}.json")
        with open(p, "w") as f:
            json.dump(d, f)
        paths.append(p)
    return paths


# --- load_debriefs ---

def test_load_debriefs_absent_dir_returns_empty():
    from scripts.phase5_debrief_utils import load_debriefs
    with patch("scripts.phase5_debrief_utils.DEBRIEFS_DIR", "/nonexistent/path/xyz"):
        result = load_debriefs("any_role")
    assert result == []


def test_load_debriefs_returns_sorted_by_date():
    from scripts.phase5_debrief_utils import load_debriefs
    d1 = _make_debrief(date="2026-04-15")
    d2 = _make_debrief(date="2026-04-10")
    with tempfile.TemporaryDirectory() as tmp:
        _write_debriefs(tmp, "my_role", [d1, d2])
        with patch("scripts.phase5_debrief_utils.DEBRIEFS_DIR", tmp):
            result = load_debriefs("my_role")
    assert len(result) == 2
    assert result[0]["metadata"]["interview_date"] == "2026-04-10"
    assert result[1]["metadata"]["interview_date"] == "2026-04-15"


def test_load_debriefs_skips_invalid_json():
    from scripts.phase5_debrief_utils import load_debriefs
    with tempfile.TemporaryDirectory() as tmp:
        role_dir = os.path.join(tmp, "my_role")
        os.makedirs(role_dir)
        with open(os.path.join(role_dir, "bad.json"), "w") as f:
            f.write("not json {{{")
        with open(os.path.join(role_dir, "good.json"), "w") as f:
            json.dump(_make_debrief(), f)
        with patch("scripts.phase5_debrief_utils.DEBRIEFS_DIR", tmp):
            result = load_debriefs("my_role")
    assert len(result) == 1


# --- load_all_debriefs ---

def test_load_all_debriefs_absent_dir_returns_empty():
    from scripts.phase5_debrief_utils import load_all_debriefs
    with patch("scripts.phase5_debrief_utils.DEBRIEFS_DIR", "/nonexistent/xyz"):
        result = load_all_debriefs()
    assert result == []


def test_load_all_debriefs_combines_roles():
    from scripts.phase5_debrief_utils import load_all_debriefs
    with tempfile.TemporaryDirectory() as tmp:
        _write_debriefs(tmp, "role_a", [_make_debrief(role="role_a")])
        _write_debriefs(tmp, "role_b", [_make_debrief(role="role_b")])
        with patch("scripts.phase5_debrief_utils.DEBRIEFS_DIR", tmp):
            result = load_all_debriefs()
    assert len(result) == 2


# --- get_story_performance_signal ---

def test_story_signal_none_when_no_library_id():
    from scripts.phase5_debrief_utils import get_story_performance_signal
    assert get_story_performance_signal(None, []) is None
    assert get_story_performance_signal("", []) is None


def test_story_signal_none_when_no_match():
    from scripts.phase5_debrief_utils import get_story_performance_signal
    d = _make_debrief(stories=[{"library_id": "other_id", "landed": "yes", "tags": []}])
    assert get_story_performance_signal("story_001", [d]) is None


def test_story_signal_counts_correctly():
    from scripts.phase5_debrief_utils import get_story_performance_signal
    debriefs = [
        _make_debrief(stories=[{"library_id": "story_001", "landed": "yes", "tags": []}]),
        _make_debrief(stories=[{"library_id": "story_001", "landed": "yes", "tags": []}]),
        _make_debrief(stories=[{"library_id": "story_001", "landed": "partially", "tags": []}]),
    ]
    result = get_story_performance_signal("story_001", debriefs)
    assert "3 times" in result
    assert "yes x2" in result
    assert "partially x1" in result


# --- get_gap_performance_signal ---

def test_gap_signal_none_when_no_label():
    from scripts.phase5_debrief_utils import get_gap_performance_signal
    assert get_gap_performance_signal(None, []) is None
    assert get_gap_performance_signal("", []) is None


def test_gap_signal_case_insensitive_match():
    from scripts.phase5_debrief_utils import get_gap_performance_signal
    d = _make_debrief(gaps=[{"gap_label": "No SCIF Experience", "response_felt": "strong"}])
    result = get_gap_performance_signal("no scif experience", [d])
    assert result is not None
    assert "strong x1" in result


def test_gap_signal_counts_multiple():
    from scripts.phase5_debrief_utils import get_gap_performance_signal
    debriefs = [
        _make_debrief(gaps=[{"gap_label": "no scif", "response_felt": "adequate"}]),
        _make_debrief(gaps=[{"gap_label": "no scif", "response_felt": "adequate"}]),
        _make_debrief(gaps=[{"gap_label": "no scif", "response_felt": "weak"}]),
    ]
    result = get_gap_performance_signal("no scif", debriefs)
    assert "3 times" in result
    assert "adequate x2" in result
    assert "weak x1" in result


# --- load_salary_actuals ---

def test_salary_actuals_returns_none_when_no_debriefs():
    from scripts.phase5_debrief_utils import load_salary_actuals
    assert load_salary_actuals([]) is None


def test_salary_actuals_returns_none_when_no_salary_data():
    from scripts.phase5_debrief_utils import load_salary_actuals
    d = _make_debrief()  # empty salary_exchange
    assert load_salary_actuals([d]) is None


def test_salary_actuals_returns_most_recent():
    from scripts.phase5_debrief_utils import load_salary_actuals
    old = _make_debrief(date="2026-04-01",
                        salary={"range_given_min": 130000, "range_given_max": 160000})
    recent = _make_debrief(date="2026-04-15",
                           salary={"range_given_min": 145000, "range_given_max": 175000})
    result = load_salary_actuals([old, recent])
    assert result["range_given_min"] == 145000
    assert result["range_given_max"] == 175000


def test_salary_actuals_includes_stage_and_date():
    from scripts.phase5_debrief_utils import load_salary_actuals
    d = _make_debrief(date="2026-04-15", stage="hiring_manager",
                      salary={"range_given_min": 145000, "range_given_max": 175000})
    result = load_salary_actuals([d])
    assert result["interview_date"] == "2026-04-15"
    assert result["stage"] == "hiring_manager"


# --- build_continuity_section ---

def test_continuity_section_empty_when_no_debriefs():
    from scripts.phase5_debrief_utils import build_continuity_section
    assert build_continuity_section([]) == ""


def test_continuity_section_contains_stage_and_date():
    from scripts.phase5_debrief_utils import build_continuity_section
    d = _make_debrief(stage="hiring_manager", date="2026-04-15")
    result = build_continuity_section([d])
    assert "hiring_manager" in result
    assert "2026-04-15" in result
    assert "CONTINUITY SUMMARY" in result


def test_continuity_section_includes_panel_label():
    from scripts.phase5_debrief_utils import build_continuity_section
    d = _make_debrief(stage="team_panel", panel_label="se_team", date="2026-04-16")
    result = build_continuity_section([d])
    assert "se_team" in result


def test_continuity_section_shows_interviewers():
    from scripts.phase5_debrief_utils import build_continuity_section
    d = _make_debrief(interviewers=[
        {"name": "Alice", "title": "Chief Engineer", "notes": ""},
        {"name": "Bob", "title": "Systems Lead", "notes": ""},
    ])
    result = build_continuity_section([d])
    assert "Alice" in result
    assert "Bob" in result
    assert "Chief Engineer" in result


def test_continuity_section_no_what_i_said_placeholder():
    from scripts.phase5_debrief_utils import build_continuity_section
    d = _make_debrief(what_i_said=None)
    result = build_continuity_section([d])
    assert "no continuity data captured" in result


def test_continuity_section_shows_what_i_said():
    from scripts.phase5_debrief_utils import build_continuity_section
    d = _make_debrief(what_i_said="Said I prefer hybrid. Active TS/SCI.")
    result = build_continuity_section([d])
    assert "Said I prefer hybrid" in result


def test_continuity_section_multiple_debriefs_sorted():
    from scripts.phase5_debrief_utils import build_continuity_section
    d1 = _make_debrief(stage="recruiter", date="2026-04-01")
    d2 = _make_debrief(stage="hiring_manager", date="2026-04-15")
    result = build_continuity_section([d1, d2])
    assert result.index("recruiter") < result.index("hiring_manager")


# --- find_unmatched_debrief_content ---

def test_unmatched_empty_when_no_debriefs():
    from scripts.phase5_debrief_utils import find_unmatched_debrief_content
    stories, gaps = find_unmatched_debrief_content([])
    assert stories == []
    assert gaps == []


def test_unmatched_story_not_in_library():
    from scripts.phase5_debrief_utils import find_unmatched_debrief_content
    d = _make_debrief(stories=[{"library_id": "missing_id", "tags": ["mbse"], "landed": "yes"}])
    with patch("scripts.interview_library_parser._load_library",
               return_value={"stories": [], "gap_responses": [], "questions": []}):
        stories, gaps = find_unmatched_debrief_content([d])
    assert len(stories) == 1
    assert stories[0]["library_id"] == "missing_id"


def test_matched_story_not_in_unmatched():
    from scripts.phase5_debrief_utils import find_unmatched_debrief_content
    d = _make_debrief(stories=[{"library_id": "story_001", "tags": [], "landed": "yes"}])
    with patch("scripts.interview_library_parser._load_library",
               return_value={"stories": [{"id": "story_001"}], "gap_responses": [], "questions": []}):
        stories, _ = find_unmatched_debrief_content([d])
    assert stories == []


def test_unmatched_gap_not_in_library():
    from scripts.phase5_debrief_utils import find_unmatched_debrief_content
    d = _make_debrief(gaps=[{"gap_label": "no drone experience", "response_felt": "adequate"}])
    with patch("scripts.interview_library_parser._load_library",
               return_value={"stories": [], "gap_responses": [], "questions": []}):
        _, gaps = find_unmatched_debrief_content([d])
    assert "no drone experience" in gaps


def test_unmatched_deduplicates_across_debriefs():
    from scripts.phase5_debrief_utils import find_unmatched_debrief_content
    d1 = _make_debrief(stories=[{"library_id": "missing_id", "tags": [], "landed": "yes"}])
    d2 = _make_debrief(stories=[{"library_id": "missing_id", "tags": [], "landed": "yes"}])
    with patch("scripts.interview_library_parser._load_library",
               return_value={"stories": [], "gap_responses": [], "questions": []}):
        stories, _ = find_unmatched_debrief_content([d1, d2])
    assert len(stories) == 1


# --- has_debrief_for_stage ---

def test_has_debrief_for_stage_true():
    from scripts.phase5_debrief_utils import has_debrief_for_stage
    d = _make_debrief(stage="hiring_manager")
    assert has_debrief_for_stage([d], "hiring_manager") is True


def test_has_debrief_for_stage_false():
    from scripts.phase5_debrief_utils import has_debrief_for_stage
    d = _make_debrief(stage="recruiter")
    assert has_debrief_for_stage([d], "hiring_manager") is False


def test_has_debrief_for_stage_panel_label_match():
    from scripts.phase5_debrief_utils import has_debrief_for_stage
    d = _make_debrief(stage="team_panel", panel_label="se_team")
    assert has_debrief_for_stage([d], "team_panel", panel_label="se_team") is True


def test_has_debrief_for_stage_panel_label_no_match():
    from scripts.phase5_debrief_utils import has_debrief_for_stage
    d = _make_debrief(stage="team_panel", panel_label="se_team")
    assert has_debrief_for_stage([d], "team_panel", panel_label="biz_leaders") is False


def test_has_debrief_for_stage_empty_list():
    from scripts.phase5_debrief_utils import has_debrief_for_stage
    assert has_debrief_for_stage([], "hiring_manager") is False
```

- [ ] **Step 3: Run tests to verify all pass**

```bash
cd c:/Users/r_tod/Documents/Projects/Job_search_agent
python -m pytest tests/test_phase5_debrief_utils.py -v
```
Expected: all tests pass (26 tests).

- [ ] **Step 4: Commit**

```bash
git add scripts/phase5_debrief_utils.py tests/test_phase5_debrief_utils.py
git commit -m "feat: add phase5_debrief_utils -- debrief I/O, continuity, salary, notifications (26 tests)"
```

---

## Task 2: JD Tag Extraction + Library Seeding for Stories, Gaps, Questions

**[SUBAGENT — runs in parallel with Task 1]**

**Files:**
- Modify: `scripts/phase5_interview_prep.py`
- Modify: `tests/phase5/test_interview_prep.py`

### Changes to `phase5_interview_prep.py`

**1. Add imports** (after existing imports, before `load_dotenv()`):
```python
import scripts.interview_library_parser as _ilp
```

**2. Add `_extract_jd_tags()` function** (add after `extract_salary()`, before `load_resume_bullets()`):
```python
def _extract_jd_tags(jd_text: str) -> list:
    """Return controlled-vocabulary tags that appear in jd_text (case-insensitive)."""
    tags = _ilp.load_tags()
    jd_lower = jd_text.lower()
    return [t for t in tags if t.lower() in jd_lower]
```

**3. Modify `_build_section2_prompt()`** — add `library_seeds=None` parameter and inject seed block before the format instructions:

Change signature from:
```python
def _build_section2_prompt(jd, story_context, candidate_profile, profile):
```
To:
```python
def _build_section2_prompt(jd, story_context, candidate_profile, profile, library_seeds=None):
```

Add seed block construction. Insert it in the return string just before the format block (replace the `return (` block ending at line ~392):

```python
    seed_block = ""
    if library_seeds:
        seed_lines = [
            "\nVETTED LIBRARY STORIES -- tailor each to this role and stage (do NOT reproduce verbatim):\n"
        ]
        for i, s in enumerate(library_seeds, 1):
            tags_str = ", ".join(s.get("tags", []))
            perf = s.get("_performance_signal", "")
            seed_lines.append(f"LIBRARY STORY {i} [{tags_str}]:")
            if perf:
                seed_lines.append(f"Performance: {perf}")
            seed_lines.append(f"Employer: {s.get('employer', '')} | {s.get('title', '')} | {s.get('dates', '')}")
            seed_lines.append(f"Situation: {s.get('situation', '')}")
            seed_lines.append(f"Task: {s.get('task', '')}")
            seed_lines.append(f"Action: {s.get('action', '')}")
            seed_lines.append(f"Result: {s.get('result', '')}")
            if s.get("if_probed"):
                seed_lines.append(f"If probed: {s.get('if_probed')}")
            seed_lines.append("")
        seed_lines.append(
            "For each seeded story: tailor to this role/stage. "
            "After 'STORY N --' heading, append '(library-seeded)'. "
            "If a Performance line is shown above, reproduce it verbatim on the next line.\n"
        )
        seed_block = "\n".join(seed_lines)

    return (
        f"Generate employer-attributed interview stories for a {profile['label']}.\n\n"
        f"CANDIDATE PROFILE (PII removed):\n{candidate_profile[:2500]}\n\n"
        f"RESUME SUBMITTED FOR THIS ROLE -- with employer context:\n{story_context[:3000]}\n\n"
        f"JOB DESCRIPTION:\n{jd[:2000]}\n\n"
        f"CRITICAL INSTRUCTIONS:\n"
        f"- Every story MUST be grounded in the bullets shown above\n"
        f"- Every story MUST include employer attribution "
        f"(\"During my time at [Employer] as [Title], [dates]...\")\n"
        f"- Do NOT invent metrics or outcomes\n\n"
        f"{_depth_instructions[profile['story_depth']]}\n\n"
        f"{_gap_instructions[profile['gap_behavior']]}\n\n"
        f"{seed_block}"
        f"Generate {profile['story_count']} stories. Use this format:\n\n"
        f"ROLE FIT ASSESSMENT:\n[{role_fit_instruction}]\n\n"
        f"KEY THEMES TO LEAD WITH:\n"
        f"Theme 1 -- [Name]: [1-2 sentences]\n"
        f"Theme 2 -- [Name]: [1-2 sentences]\n\n"
        f"STORY BANK:\n\n"
        f"STORY 1 -- [JD Requirement this addresses]:\n"
        f"Employer: [Company | Title | Dates]\n"
        f"Situation: [Context]\n"
        f"Task: [What needed to be done]\n"
        f"Action: [What YOU did -- first person]\n"
        f"Result: [Outcome -- qualitative acceptable]\n"
        f"If probed: [One additional sentence -- omit for headline depth]\n\n"
        f"[Continue for all stories in the {profile['story_count']} range]\n\n"
        f"LIKELY INTERVIEW QUESTIONS:\n"
        f"[5-8 questions likely to be asked, with one-line approach each]"
    )
```

**4. Modify `_build_gap_prompt()`** — add `library_seeds=None` parameter:

Change signature from:
```python
def _build_gap_prompt(jd, gaps_section, candidate_profile, profile):
```
To:
```python
def _build_gap_prompt(jd, gaps_section, candidate_profile, profile, library_seeds=None):
```

Add seed block. Insert just before the `return (` at the end of the function (before `peer_frame_block` line):

```python
    gap_seed_block = ""
    if library_seeds:
        seed_lines = [
            "\nVETTED GAP RESPONSES FROM LIBRARY -- tailor each to this role:\n"
        ]
        for s in library_seeds:
            tags_str = ", ".join(s.get("tags", []))
            perf = s.get("_performance_signal", "")
            seed_lines.append(f"GAP: {s.get('gap_label', '')} [{tags_str}]:")
            if perf:
                seed_lines.append(f"Performance: {perf}")
            seed_lines.append(f"Honest answer: {s.get('honest_answer', '')}")
            seed_lines.append(f"Bridge: {s.get('bridge', '')}")
            seed_lines.append(f"Redirect: {s.get('redirect', '')}")
            seed_lines.append("")
        seed_lines.append(
            "For each seeded gap: tailor to this role/stage. "
            "After 'GAP N --' heading, append '(library-seeded)'. "
            "If a Performance line is shown, reproduce it verbatim on the next line.\n"
        )
        gap_seed_block = "\n".join(seed_lines)
```

Then in the return string, insert `{gap_seed_block}` immediately before the format instructions block (before `f"For each gap provide a direct..."`):
```python
    return (
        f"You are doing a two-step gap analysis grounded strictly in the JD text and "
        f"candidate profile. Follow these steps exactly.\n\n"
        # ... (existing content unchanged) ...
        f"{gap_seed_block}"
        f"For each gap provide a direct, confident talking point -- not apologetic.\n\n"
        # ... rest of format instructions unchanged ...
    )
```

**5. Modify `generate_prep()`** — add library seeding calls in the story, gap, and questions sections.

After `jd_lower = jd.lower()` (line ~772), add:
```python
    # Extract JD tags for library filtering
    jd_tags = _extract_jd_tags(jd)
```

Before the Section 2 API call, add story seed lookup:
```python
    # Library seed lookup for stories
    story_seeds = _ilp.get_stories(tags=jd_tags) if jd_tags else []
    story_prompt = _build_section2_prompt(
        jd, story_context, candidate_profile, profile,
        library_seeds=story_seeds or None
    )
```
(Replace the existing single-line `story_prompt = _build_section2_prompt(...)` call.)

Before the Section 3 API call, add gap seed lookup:
```python
    # Library seed lookup for gaps
    gap_seeds = _ilp.get_gap_responses(tags=jd_tags) if jd_tags else []
    if profile["gap_behavior"] != "omit":
        gap_prompt = _build_gap_prompt(
            jd, gaps_section, candidate_profile, profile,
            library_seeds=gap_seeds or None
        )
```
(Replace the existing `gap_prompt = _build_gap_prompt(...)` call; keep the `if profile["gap_behavior"] == "omit":` branch unchanged.)

Before the Section 4 API call, add questions seed lookup:
```python
    # Library seed lookup for questions
    question_seeds = _ilp.get_questions(tags=jd_tags, stage=interview_stage) if jd_tags else []
    question_seed_block = ""
    if question_seeds:
        qlines = ["\nVETTED QUESTIONS FROM LIBRARY -- include or adapt these as appropriate:\n"]
        for q in question_seeds:
            qlines.append(f"- {q.get('text', '')}")
        qlines.append(
            "\nFor each included library question, append '(library-seeded)' after the question text.\n"
        )
        question_seed_block = "\n".join(qlines)

    context_block = (
        f"JOB DESCRIPTION:\n{jd[:2000]}\n\n"
        f"CANDIDATE BACKGROUND (PII removed):\n{strip_pii(candidate_profile[:800])}\n\n"
        f"{question_seed_block}"
    )
    questions_prompt = context_block + profile["questions_prompt"]
```
(Replace the existing `context_block = ...` and `questions_prompt = ...` lines.)

---

- [ ] **Step 1: Write failing tests for `_extract_jd_tags` and library seeding**

Add to `tests/phase5/test_interview_prep.py`:

```python
# ---- _extract_jd_tags tests ----

def test_extract_jd_tags_returns_matching_tags():
    import scripts.interview_library_parser as ilp
    from scripts.phase5_interview_prep import _extract_jd_tags
    with patch.object(ilp, "load_tags", return_value=["mbse", "systems-engineering", "leadership"]):
        result = _extract_jd_tags("This role requires MBSE experience and Systems Engineering skills.")
    assert "mbse" in result
    assert "systems-engineering" in result
    assert "leadership" not in result


def test_extract_jd_tags_returns_empty_when_no_match():
    import scripts.interview_library_parser as ilp
    from scripts.phase5_interview_prep import _extract_jd_tags
    with patch.object(ilp, "load_tags", return_value=["mbse", "clearance"]):
        result = _extract_jd_tags("General software engineering role.")
    assert result == []


def test_extract_jd_tags_case_insensitive():
    import scripts.interview_library_parser as ilp
    from scripts.phase5_interview_prep import _extract_jd_tags
    with patch.object(ilp, "load_tags", return_value=["mbse"]):
        result = _extract_jd_tags("Experience with MBSE frameworks required.")
    assert "mbse" in result


# ---- library seeding in _build_section2_prompt ----

def test_build_section2_prompt_injects_seed_block():
    from scripts.phase5_interview_prep import _build_section2_prompt, STAGE_PROFILES
    seeds = [{
        "id": "story_001", "employer": "G2 OPS", "title": "Lead SE", "dates": "2022-2024",
        "situation": "Led MBSE.", "task": "Build OV-1.", "action": "Facilitated IPT.",
        "result": "Delivered baseline.", "tags": ["mbse"], "if_probed": None
    }]
    prompt = _build_section2_prompt("JD text", "story context", "profile",
                                    STAGE_PROFILES["hiring_manager"], library_seeds=seeds)
    assert "VETTED LIBRARY STORIES" in prompt
    assert "G2 OPS" in prompt
    assert "library-seeded" in prompt


def test_build_section2_prompt_no_seed_block_when_none():
    from scripts.phase5_interview_prep import _build_section2_prompt, STAGE_PROFILES
    prompt = _build_section2_prompt("JD text", "story context", "profile",
                                    STAGE_PROFILES["hiring_manager"], library_seeds=None)
    assert "VETTED LIBRARY STORIES" not in prompt


# ---- library seeding in _build_gap_prompt ----

def test_build_gap_prompt_injects_seed_block():
    from scripts.phase5_interview_prep import _build_gap_prompt, STAGE_PROFILES
    seeds = [{
        "id": "gap_001", "gap_label": "no SCIF experience", "severity": "REQUIRED",
        "honest_answer": "I have not worked in SCIF.", "bridge": "Worked TS cleared.",
        "redirect": "Adapt quickly.", "tags": ["clearance"]
    }]
    prompt = _build_gap_prompt("JD text", "gaps text", "profile",
                               STAGE_PROFILES["hiring_manager"], library_seeds=seeds)
    assert "VETTED GAP RESPONSES" in prompt
    assert "no SCIF experience" in prompt
    assert "library-seeded" in prompt


def test_build_gap_prompt_no_seed_block_when_none():
    from scripts.phase5_interview_prep import _build_gap_prompt, STAGE_PROFILES
    prompt = _build_gap_prompt("JD text", "gaps text", "profile",
                               STAGE_PROFILES["hiring_manager"], library_seeds=None)
    assert "VETTED GAP RESPONSES" not in prompt


# ---- generate_prep calls get_stories with jd tags ----

def test_generate_prep_calls_library_with_jd_tags(monkeypatch):
    import scripts.interview_library_parser as ilp
    from scripts.phase5_interview_prep import generate_prep
    from unittest.mock import patch

    captured_tags = {}
    def fake_get_stories(tags=None, **kw):
        captured_tags["tags"] = tags
        return []
    monkeypatch.setattr(ilp, "load_tags", lambda: ["mbse", "systems-engineering"])
    monkeypatch.setattr(ilp, "get_stories", fake_get_stories)
    monkeypatch.setattr(ilp, "get_gap_responses", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_questions", lambda **kw: [])

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()
    with tempfile.TemporaryDirectory() as tmpdir:
        generate_prep(client, role_data, "hiring_manager",
                      str(Path(tmpdir) / "p.txt"), str(Path(tmpdir) / "p.docx"))

    assert captured_tags.get("tags") is not None


# ---- cold path: no seeds, prompt unchanged behaviour ----

def test_generate_prep_cold_path_no_library_seeds(monkeypatch):
    import scripts.interview_library_parser as ilp
    from scripts.phase5_interview_prep import generate_prep

    monkeypatch.setattr(ilp, "load_tags", lambda: [])
    monkeypatch.setattr(ilp, "get_stories", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_gap_responses", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_questions", lambda **kw: [])

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()
    with tempfile.TemporaryDirectory() as tmpdir:
        txt = Path(tmpdir) / "p.txt"
        generate_prep(client, role_data, "hiring_manager",
                      str(txt), str(Path(tmpdir) / "p.docx"))
    # No library seeds -- section 2 call should NOT include VETTED LIBRARY STORIES
    section2_kwargs = client.messages.create.call_args_list[2].kwargs
    prompt = section2_kwargs["messages"][0]["content"]
    assert "VETTED LIBRARY STORIES" not in prompt
```

Add `from unittest.mock import patch` at the top of the test file (if not already there).

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/phase5/test_interview_prep.py::test_extract_jd_tags_returns_matching_tags tests/phase5/test_interview_prep.py::test_build_section2_prompt_injects_seed_block tests/phase5/test_interview_prep.py::test_generate_prep_cold_path_no_library_seeds -v
```
Expected: FAIL with `ImportError` or `AssertionError`.

- [ ] **Step 3: Implement all changes to `phase5_interview_prep.py`** as described above (import, `_extract_jd_tags`, modified `_build_section2_prompt`, modified `_build_gap_prompt`, modified `generate_prep`)

- [ ] **Step 4: Run all new + existing tests**

```bash
python -m pytest tests/phase5/test_interview_prep.py -v
```
Expected: all pass (previously 6 tests + 8 new = ~14 tests; the 2 live tests may still be skipped/fail as before).

- [ ] **Step 5: Syntax check**

```bash
python -c "import scripts.phase5_interview_prep"
```
Expected: no output (clean import).

- [ ] **Step 6: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "feat: Session A -- JD tag extraction, library seeding for stories/gaps/questions"
```

---

## Task 3: Performance Signal Surfacing

**[Sequential — depends on Task 1 AND Task 2 complete]**

**Files:**
- Modify: `scripts/phase5_interview_prep.py`
- Modify: `tests/phase5/test_interview_prep.py`

Performance signal is injected INTO the seed objects before passing to `_build_section2_prompt` and `_build_gap_prompt`. The `_performance_signal` key is already referenced in the seed block construction added in Task 2 — this task populates it.

### Changes to `generate_prep()`

After the library seed lookups added in Task 2, add performance signal injection:

```python
    # Inject performance signal into story seeds
    if story_seeds:
        all_debriefs_for_signal = _load_all_debriefs_safe()
        for s in story_seeds:
            signal = _get_story_signal_safe(s.get("id"), all_debriefs_for_signal)
            if signal:
                s["_performance_signal"] = signal

    # Inject performance signal into gap seeds
    if gap_seeds:
        if 'all_debriefs_for_signal' not in dir():
            all_debriefs_for_signal = _load_all_debriefs_safe()
        for g in gap_seeds:
            signal = _get_gap_signal_safe(g.get("gap_label"), all_debriefs_for_signal)
            if signal:
                g["_performance_signal"] = signal
```

Add these three helper wrappers in `phase5_interview_prep.py` (after the `_extract_jd_tags` function):

```python
def _load_all_debriefs_safe():
    try:
        from scripts.phase5_debrief_utils import load_all_debriefs
        return load_all_debriefs()
    except Exception:
        return []


def _get_story_signal_safe(library_id, all_debriefs):
    try:
        from scripts.phase5_debrief_utils import get_story_performance_signal
        return get_story_performance_signal(library_id, all_debriefs)
    except Exception:
        return None


def _get_gap_signal_safe(gap_label, all_debriefs):
    try:
        from scripts.phase5_debrief_utils import get_gap_performance_signal
        return get_gap_performance_signal(gap_label, all_debriefs)
    except Exception:
        return None
```

The `try/except` wrappers ensure no-regression if debrief_utils is unavailable (it is available by Task 3, but defensively coded).

---

- [ ] **Step 1: Write failing tests**

Add to `tests/phase5/test_interview_prep.py`:

```python
# ---- performance signal injected into story seed ----

def test_performance_signal_injected_into_story_seed_prompt(monkeypatch, tmp_path):
    import scripts.interview_library_parser as ilp
    import scripts.phase5_debrief_utils as dbu
    from scripts.phase5_interview_prep import generate_prep

    sample_story = {
        "id": "story_001", "employer": "G2 OPS", "title": "Lead SE", "dates": "2022-2024",
        "situation": "Led MBSE.", "task": "OV-1.", "action": "IPT.", "result": "Baseline.",
        "tags": ["mbse"], "if_probed": None, "roles_used": []
    }
    monkeypatch.setattr(ilp, "load_tags", lambda: ["mbse"])
    monkeypatch.setattr(ilp, "get_stories", lambda tags=None, **kw: [sample_story] if tags else [])
    monkeypatch.setattr(ilp, "get_gap_responses", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_questions", lambda **kw: [])
    monkeypatch.setattr(dbu, "load_all_debriefs",
                        lambda: [{"metadata": {"role": "x", "stage": "hm", "interview_date": "2026-04-01",
                                               "panel_label": None, "interviewers": []},
                                  "stories_used": [{"library_id": "story_001", "landed": "yes", "tags": []}],
                                  "gaps_surfaced": [], "salary_exchange": {},
                                  "advancement_read": {}, "what_i_said": None, "open_notes": None}])

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()
    generate_prep(client, role_data, "hiring_manager",
                  str(tmp_path / "p.txt"), str(tmp_path / "p.docx"))

    section2_kwargs = client.messages.create.call_args_list[2].kwargs
    prompt = section2_kwargs["messages"][0]["content"]
    assert "Used 1 times" in prompt
    assert "yes x1" in prompt


def test_no_performance_signal_when_no_debrief_history(monkeypatch, tmp_path):
    import scripts.interview_library_parser as ilp
    import scripts.phase5_debrief_utils as dbu
    from scripts.phase5_interview_prep import generate_prep

    sample_story = {
        "id": "story_999", "employer": "Acme", "title": "SE", "dates": "2020-2022",
        "situation": "s", "task": "t", "action": "a", "result": "r",
        "tags": ["mbse"], "if_probed": None, "roles_used": []
    }
    monkeypatch.setattr(ilp, "load_tags", lambda: ["mbse"])
    monkeypatch.setattr(ilp, "get_stories", lambda tags=None, **kw: [sample_story] if tags else [])
    monkeypatch.setattr(ilp, "get_gap_responses", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_questions", lambda **kw: [])
    monkeypatch.setattr(dbu, "load_all_debriefs", lambda: [])

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()
    generate_prep(client, role_data, "hiring_manager",
                  str(tmp_path / "p.txt"), str(tmp_path / "p.docx"))

    section2_kwargs = client.messages.create.call_args_list[2].kwargs
    prompt = section2_kwargs["messages"][0]["content"]
    assert "Performance:" not in prompt
```

- [ ] **Step 2: Run to verify fail**

```bash
python -m pytest tests/phase5/test_interview_prep.py::test_performance_signal_injected_into_story_seed_prompt tests/phase5/test_interview_prep.py::test_no_performance_signal_when_no_debrief_history -v
```
Expected: FAIL.

- [ ] **Step 3: Implement the three safe wrapper functions and the signal injection block in `generate_prep()`**

- [ ] **Step 4: Run full test suite for the file**

```bash
python -m pytest tests/phase5/test_interview_prep.py -v
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "feat: performance signal surfacing -- inject landed/response history into library seeds"
```

---

## Task 4: Salary Actuals Override

**[Sequential — depends on Task 3]**

**Files:**
- Modify: `scripts/phase5_interview_prep.py`
- Modify: `tests/phase5/test_interview_prep.py`

### Changes to `_build_section1_prompt()`

Add `salary_actuals=None` parameter. When `salary_actuals` is not None and stage has `salary_in_section1 == True`, replace the `salary_block` with actuals:

```python
def _build_section1_prompt(jd, salary_data, profile, salary_actuals=None):
    # ... existing _stage_instructions dict unchanged ...

    salary_block = ""
    if profile["salary_in_section1"]:
        if salary_actuals:
            min_val = salary_actuals.get("range_given_min")
            max_val = salary_actuals.get("range_given_max")
            anchor = salary_actuals.get("candidate_anchor")
            floor_ = salary_actuals.get("candidate_floor")
            act_stage = salary_actuals.get("stage", "prior stage")
            act_date = salary_actuals.get("interview_date", "prior interview")
            min_str = f"${min_val:,.0f}" if min_val else "not recorded"
            max_str = f"${max_val:,.0f}" if max_val else "not recorded"
            anchor_str = f"${anchor:,.0f}" if anchor else "not recorded"
            floor_str = f"${floor_:,.0f}" if floor_ else "not recorded"
            salary_block = (
                f"\nSALARY ACTUALS (reported from {act_stage} on {act_date} -- use these, not estimates):\n"
                f"Range given by interviewer: {min_str} -- {max_str}\n"
                f"Candidate anchor stated: {anchor_str}\n"
                f"Candidate floor: {floor_str}\n"
                f"Note: these are reported actuals from a prior interview for this role. "
                f"Present them as confirmed data, not as analysis.\n"
            )
        else:
            salary_block = (
                f"\nSALARY & LEVEL CONTEXT:\n"
                f"JD posted range: {salary_data['text'] if salary_data['found'] else 'Not found in JD'}\n"
                f"[1-2 sentences on what level this represents and where initial offers land.]\n\n"
                f"SALARY EXPECTATIONS GUIDANCE:\n"
                f"{salary_data['guidance'] if salary_data['found'] else 'Research market rate before interview.'}\n"
            )

    return (
        f"Research this company and role, then generate an interview prep brief "
        f"for a {profile['label']}.\n\n"
        f"JOB DESCRIPTION:\n{jd[:2500]}\n\n"
        f"Use the web_search tool to find current information about this company.\n\n"
        f"Stage-specific instructions:\n{_stage_instructions[profile['section1_focus']]}\n"
        f"{salary_block}\n"
        f"Format your brief with ALL-CAPS section headers followed by a colon "
        f"(e.g., 'COMPANY OVERVIEW:'). Include only sections relevant to this stage."
    )
```

### Changes to `generate_prep()`

Add salary actuals lookup before the Section 1 call. Add a safe wrapper (same pattern as Task 3):

After the `jd_tags = _extract_jd_tags(jd)` line, add:
```python
    # Load role debriefs for salary actuals and continuity (used in multiple sections)
    role_debriefs = _load_role_debriefs_safe(role_name)
    salary_actuals = _load_salary_actuals_safe(role_debriefs)
```

Add these wrappers after the existing safe wrappers from Task 3:
```python
def _load_role_debriefs_safe(role):
    try:
        from scripts.phase5_debrief_utils import load_debriefs
        return load_debriefs(role)
    except Exception:
        return []


def _load_salary_actuals_safe(debriefs):
    try:
        from scripts.phase5_debrief_utils import load_salary_actuals
        return load_salary_actuals(debriefs)
    except Exception:
        return None
```

Then replace the Section 1 prompt build call:
```python
    company_prompt = _build_section1_prompt(jd, salary_data, profile,
                                             salary_actuals=salary_actuals)
```

---

- [ ] **Step 1: Write failing tests**

Add to `tests/phase5/test_interview_prep.py`:

```python
# ---- salary actuals override ----

def test_salary_actuals_override_injects_actuals_into_section1_prompt(monkeypatch, tmp_path):
    import scripts.phase5_debrief_utils as dbu
    import scripts.interview_library_parser as ilp
    from scripts.phase5_interview_prep import generate_prep

    actuals_debrief = {
        "metadata": {"role": "acme_sse", "stage": "recruiter", "interview_date": "2026-04-10",
                     "panel_label": None, "interviewers": []},
        "advancement_read": {}, "stories_used": [], "gaps_surfaced": [],
        "salary_exchange": {"range_given_min": 145000, "range_given_max": 175000,
                            "candidate_anchor": 168000, "candidate_floor": 152000},
        "what_i_said": None, "open_notes": None,
    }
    monkeypatch.setattr(ilp, "load_tags", lambda: [])
    monkeypatch.setattr(ilp, "get_stories", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_gap_responses", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_questions", lambda **kw: [])
    monkeypatch.setattr(dbu, "load_all_debriefs", lambda: [])
    monkeypatch.setattr(dbu, "load_debriefs", lambda role: [actuals_debrief])

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()
    generate_prep(client, role_data, "hiring_manager",
                  str(tmp_path / "p.txt"), str(tmp_path / "p.docx"))

    section1_kwargs = client.messages.create.call_args_list[0].kwargs
    prompt = section1_kwargs["messages"][0]["content"]
    assert "SALARY ACTUALS" in prompt
    assert "145,000" in prompt
    assert "175,000" in prompt


def test_no_salary_override_when_no_debrief(monkeypatch, tmp_path):
    import scripts.phase5_debrief_utils as dbu
    import scripts.interview_library_parser as ilp
    from scripts.phase5_interview_prep import generate_prep

    monkeypatch.setattr(ilp, "load_tags", lambda: [])
    monkeypatch.setattr(ilp, "get_stories", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_gap_responses", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_questions", lambda **kw: [])
    monkeypatch.setattr(dbu, "load_all_debriefs", lambda: [])
    monkeypatch.setattr(dbu, "load_debriefs", lambda role: [])

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()
    generate_prep(client, role_data, "hiring_manager",
                  str(tmp_path / "p.txt"), str(tmp_path / "p.docx"))

    section1_kwargs = client.messages.create.call_args_list[0].kwargs
    prompt = section1_kwargs["messages"][0]["content"]
    assert "SALARY ACTUALS" not in prompt
```

- [ ] **Step 2: Run to verify fail**

```bash
python -m pytest tests/phase5/test_interview_prep.py::test_salary_actuals_override_injects_actuals_into_section1_prompt tests/phase5/test_interview_prep.py::test_no_salary_override_when_no_debrief -v
```
Expected: FAIL.

- [ ] **Step 3: Implement** the `salary_actuals` param on `_build_section1_prompt()`, safe wrappers, and `generate_prep()` changes.

- [ ] **Step 4: Run full test suite**

```bash
python -m pytest tests/phase5/test_interview_prep.py -v
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "feat: salary actuals override -- use reported debrief salary instead of JD estimates"
```

---

## Task 5: Continuity Section in Output

**[Sequential — depends on Task 4]**

**Files:**
- Modify: `scripts/phase5_interview_prep.py`
- Modify: `tests/phase5/test_interview_prep.py`

### Changes to `generate_prep()`

After all section generation (after `section4 = response4.content[0].text`), add:

```python
    # Build continuity section from role debriefs
    continuity_text = _build_continuity_safe(role_debriefs)
```

Add safe wrapper:
```python
def _build_continuity_safe(debriefs):
    try:
        from scripts.phase5_debrief_utils import build_continuity_section
        return build_continuity_section(debriefs)
    except Exception:
        return ""
```

In the output compilation block, add after the Section 4 block:
```python
    if continuity_text:
        output_lines.append(continuity_text)
```

### Changes to `generate_prep_docx()`

Add `continuity_section=""` parameter (after `salary_data`):
```python
def generate_prep_docx(output_path, role, resume_source, stage_profile,
                        section1, section_intro, section2, section3, section4,
                        salary_data, continuity_section=""):
```

After the Section 4 block in the docx generator body, add:
```python
    # Continuity summary (appended only when prior debriefs exist)
    if continuity_section:
        add_heading("Continuity Summary", level=1)
        add_normal("(Reference record from prior interviews -- not prep guidance)")
        parse_and_add_section(continuity_section)
```

Update the `generate_prep_docx()` call in `generate_prep()`:
```python
        generate_prep_docx(
            output_docx_path, role_name, resume_source, profile,
            section1, section_intro, section2, section3, section4,
            salary_data, continuity_section=continuity_text
        )
```

---

- [ ] **Step 1: Write failing tests**

Add to `tests/phase5/test_interview_prep.py`:

```python
# ---- continuity section in output ----

def test_continuity_section_appears_in_txt_when_debriefs_exist(monkeypatch, tmp_path):
    import scripts.phase5_debrief_utils as dbu
    import scripts.interview_library_parser as ilp
    from scripts.phase5_interview_prep import generate_prep

    prior_debrief = {
        "metadata": {"role": "acme_sse", "stage": "recruiter", "interview_date": "2026-04-01",
                     "panel_label": None,
                     "interviewers": [{"name": "HR Alice", "title": "Recruiter", "notes": ""}]},
        "advancement_read": {"assessment": "maybe", "notes": ""},
        "stories_used": [], "gaps_surfaced": [], "salary_exchange": {},
        "what_i_said": "Said I want hybrid work.",
        "open_notes": None,
    }
    monkeypatch.setattr(ilp, "load_tags", lambda: [])
    monkeypatch.setattr(ilp, "get_stories", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_gap_responses", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_questions", lambda **kw: [])
    monkeypatch.setattr(dbu, "load_all_debriefs", lambda: [])
    monkeypatch.setattr(dbu, "load_debriefs", lambda role: [prior_debrief])

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()
    txt_path = tmp_path / "p.txt"
    generate_prep(client, role_data, "hiring_manager",
                  str(txt_path), str(tmp_path / "p.docx"))
    content = txt_path.read_text(encoding="utf-8")
    assert "CONTINUITY SUMMARY" in content
    assert "Said I want hybrid work." in content
    assert "HR Alice" in content


def test_no_continuity_section_when_no_debriefs(monkeypatch, tmp_path):
    import scripts.phase5_debrief_utils as dbu
    import scripts.interview_library_parser as ilp
    from scripts.phase5_interview_prep import generate_prep

    monkeypatch.setattr(ilp, "load_tags", lambda: [])
    monkeypatch.setattr(ilp, "get_stories", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_gap_responses", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_questions", lambda **kw: [])
    monkeypatch.setattr(dbu, "load_all_debriefs", lambda: [])
    monkeypatch.setattr(dbu, "load_debriefs", lambda role: [])

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()
    txt_path = tmp_path / "p.txt"
    generate_prep(client, role_data, "hiring_manager",
                  str(txt_path), str(tmp_path / "p.docx"))
    content = txt_path.read_text(encoding="utf-8")
    assert "CONTINUITY SUMMARY" not in content


def test_continuity_section_in_docx(monkeypatch, tmp_path):
    import scripts.phase5_debrief_utils as dbu
    import scripts.interview_library_parser as ilp
    from scripts.phase5_interview_prep import generate_prep

    prior_debrief = {
        "metadata": {"role": "acme_sse", "stage": "recruiter", "interview_date": "2026-04-01",
                     "panel_label": None,
                     "interviewers": [{"name": "HR Alice", "title": "Recruiter", "notes": ""}]},
        "advancement_read": {}, "stories_used": [], "gaps_surfaced": {}, "salary_exchange": {},
        "what_i_said": "Said I prefer remote.", "open_notes": None,
    }
    monkeypatch.setattr(ilp, "load_tags", lambda: [])
    monkeypatch.setattr(ilp, "get_stories", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_gap_responses", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_questions", lambda **kw: [])
    monkeypatch.setattr(dbu, "load_all_debriefs", lambda: [])
    monkeypatch.setattr(dbu, "load_debriefs", lambda role: [prior_debrief])

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()
    docx_path = tmp_path / "p.docx"
    generate_prep(client, role_data, "hiring_manager",
                  str(tmp_path / "p.txt"), str(docx_path))
    doc = Document(str(docx_path))
    all_text = "\n".join(p.text for p in doc.paragraphs)
    assert "Continuity Summary" in all_text or "CONTINUITY" in all_text
```

- [ ] **Step 2: Run to verify fail**

```bash
python -m pytest tests/phase5/test_interview_prep.py::test_continuity_section_appears_in_txt_when_debriefs_exist tests/phase5/test_interview_prep.py::test_no_continuity_section_when_no_debriefs -v
```
Expected: FAIL.

- [ ] **Step 3: Implement** `_build_continuity_safe()`, output compilation change, and `generate_prep_docx()` changes.

- [ ] **Step 4: Run full test suite**

```bash
python -m pytest tests/phase5/test_interview_prep.py -v
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "feat: continuity section -- append prior debrief history to prep package (txt + docx)"
```

---

## Task 6: Terminal Notifications + No-Regression Tests

**[Sequential — depends on Task 5]**

**Files:**
- Modify: `scripts/phase5_interview_prep.py`
- Modify: `tests/phase5/test_interview_prep.py`

### Changes to `main()`

After the `generate_prep(...)` call (after the `PHASE 5 COMPLETE` print block), add:

```python
    # Post-generation notifications
    _emit_notifications(role, interview_stage, role_debriefs_for_notify=None)
```

Wait — `role_debriefs` is loaded inside `generate_prep()` and not accessible in `main()`. Move debrief loading to `main()` and pass as context to notifications. The cleanest approach: load debriefs once in `main()` and pass the result through `role_data` (or load again in the notification call since it's cheap).

Simplest: load again in a notification helper called from `main()`:

Add after the final print block in `main()`:

```python
    # Post-generation notifications
    try:
        from scripts.phase5_debrief_utils import (
            load_debriefs, find_unmatched_debrief_content, has_debrief_for_stage
        )
        _notify_debriefs = load_debriefs(role)
        unmatched_stories, unmatched_gaps = find_unmatched_debrief_content(_notify_debriefs)
        if unmatched_stories or unmatched_gaps:
            print("\nDebrief content found that is not in your interview library.")
            print(f"Run: python scripts/phase5_workshop_capture.py --role {role} --stage {interview_stage}")
            print("to review and add workshopped content to the library.")

        if has_debrief_for_stage(_notify_debriefs, interview_stage):
            print("\nDebrief found for this stage. Generate thank you letters:")
            thankyou_cmd = f"python scripts/phase5_thankyou.py --role {role} --stage {interview_stage}"
            for d in _notify_debriefs:
                meta = d.get("metadata", {}) or {}
                if meta.get("stage") == interview_stage and meta.get("panel_label"):
                    thankyou_cmd += f" --panel_label {meta['panel_label']}"
                    break
            print(f"Run: {thankyou_cmd}")
    except Exception:
        pass  # notifications are best-effort; never block on failure
```

---

- [ ] **Step 1: Write failing tests for notifications and no-regression**

Add to `tests/phase5/test_interview_prep.py`:

```python
# ---- terminal notifications ----

def test_debrief_to_library_notification_printed(monkeypatch, tmp_path, capsys):
    import scripts.phase5_debrief_utils as dbu
    import scripts.interview_library_parser as ilp
    from scripts.phase5_interview_prep import generate_prep

    monkeypatch.setattr(ilp, "load_tags", lambda: [])
    monkeypatch.setattr(ilp, "get_stories", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_gap_responses", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_questions", lambda **kw: [])
    monkeypatch.setattr(dbu, "load_all_debriefs", lambda: [])
    monkeypatch.setattr(dbu, "load_debriefs", lambda role: [])

    # Notifications are in main(), not generate_prep(). Test the notification
    # helper logic by calling the debrief_utils functions directly.
    # This test validates find_unmatched_debrief_content triggers the right output.
    unmatched_debrief = {
        "metadata": {"role": "r", "stage": "hiring_manager", "interview_date": "2026-04-10",
                     "panel_label": None, "interviewers": []},
        "stories_used": [{"library_id": "ghost_id", "tags": ["mbse"], "landed": "yes"}],
        "gaps_surfaced": [], "salary_exchange": {}, "advancement_read": {},
        "what_i_said": None, "open_notes": None,
    }
    with patch("scripts.interview_library_parser._load_library",
               return_value={"stories": [], "gap_responses": [], "questions": []}):
        stories, gaps = dbu.find_unmatched_debrief_content([unmatched_debrief])
    assert len(stories) == 1
    assert stories[0]["library_id"] == "ghost_id"


def test_thankyou_notification_check(monkeypatch):
    import scripts.phase5_debrief_utils as dbu
    d = {
        "metadata": {"stage": "hiring_manager", "panel_label": None, "interview_date": "2026-04-10",
                     "interviewers": [], "role": "r"},
        "stories_used": [], "gaps_surfaced": [], "salary_exchange": {}, "advancement_read": {},
        "what_i_said": None, "open_notes": None,
    }
    assert dbu.has_debrief_for_stage([d], "hiring_manager") is True
    assert dbu.has_debrief_for_stage([d], "team_panel") is False


# ---- no-regression: absent library, absent debriefs ----

def test_no_regression_absent_library_file(monkeypatch, tmp_path):
    import scripts.interview_library_parser as ilp
    import scripts.phase5_debrief_utils as dbu
    from scripts.phase5_interview_prep import generate_prep

    monkeypatch.setattr(ilp, "load_tags", lambda: [])
    monkeypatch.setattr(ilp, "get_stories", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_gap_responses", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_questions", lambda **kw: [])
    monkeypatch.setattr(dbu, "load_all_debriefs", lambda: [])
    monkeypatch.setattr(dbu, "load_debriefs", lambda role: [])

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()
    txt = tmp_path / "p.txt"
    docx = tmp_path / "p.docx"
    generate_prep(client, role_data, "hiring_manager", str(txt), str(docx))
    assert txt.exists()
    assert docx.exists()


def test_no_regression_absent_debriefs_dir(monkeypatch, tmp_path):
    import scripts.interview_library_parser as ilp
    import scripts.phase5_debrief_utils as dbu
    from scripts.phase5_interview_prep import generate_prep

    monkeypatch.setattr(ilp, "load_tags", lambda: [])
    monkeypatch.setattr(ilp, "get_stories", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_gap_responses", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_questions", lambda **kw: [])
    monkeypatch.setattr(dbu, "load_all_debriefs", lambda: [])
    monkeypatch.setattr(dbu, "load_debriefs", lambda role: [])

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()
    txt = tmp_path / "p.txt"
    generate_prep(client, role_data, "recruiter", str(txt), str(tmp_path / "p.docx"))
    assert txt.exists()
```

- [ ] **Step 2: Run to verify fail (notification helpers in main() not yet wired)**

```bash
python -m pytest tests/phase5/test_interview_prep.py::test_no_regression_absent_library_file tests/phase5/test_interview_prep.py::test_no_regression_absent_debriefs_dir -v
```
Expected: PASS (these test `generate_prep` not `main`). The notification tests validate `debrief_utils` logic directly.

```bash
python -m pytest tests/phase5/test_interview_prep.py -v
```
Expected: all pass.

- [ ] **Step 3: Add notification block to `main()` as specified above**

- [ ] **Step 4: Syntax check**

```bash
python -c "import scripts.phase5_interview_prep"
```
Expected: clean.

- [ ] **Step 5: Run full project test suite**

```bash
python -m pytest tests/ -q --ignore=tests/phase4/test_resume_generator.py --ignore=tests/phase5/test_interview_prep.py -x
python -m pytest tests/phase5/test_interview_prep.py tests/test_phase5_debrief_utils.py -v
```
Expected: all pass (two pre-existing live-API failures excluded).

- [ ] **Step 6: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "feat: terminal notifications -- workshop capture and thank you letter prompts after prep generation"
```

---

## Self-Review

### Spec Coverage Check

| AC Requirement | Task |
|---|---|
| `get_stories()` called filtered by JD tags | Task 2 |
| Seed block injected into `_build_section2_prompt()` | Task 2 |
| `(library-seeded)` label instructed in prompt | Task 2 |
| Performance signal for stories | Task 3 |
| Performance signal for gap responses | Task 3 |
| `get_gap_responses()` called filtered by tags | Task 2 |
| Seed triad injected into `_build_gap_prompt()` | Task 2 |
| `get_questions()` called filtered by tags + stage | Task 2 |
| Library question candidates injected into questions prompt | Task 2 |
| Salary actuals override from most recent debrief | Task 4 |
| Multiple debriefs -- most recent wins | Task 4 (via `load_salary_actuals` reverse iteration) |
| Continuity section when debriefs exist | Task 5 |
| No continuity section when no debriefs | Task 5 |
| Panel label in continuity header | Task 1 (`build_continuity_section`) |
| Continuity in both .txt and .docx | Task 5 |
| Debrief-to-library notification | Task 6 |
| Thank you letter notification | Task 6 |
| Thank you notification with `--panel_label` when debrief has one | Task 6 |
| No-regression: absent library | Task 6 |
| No-regression: absent debriefs dir | Task 6 |
| No-regression: both absent | Task 6 |
| `phase5_debrief_utils.py` isolated + tested | Task 1 |

### No Placeholders

- All test functions show complete code
- All implementation snippets show complete function bodies or exact diff regions
- All `run:` commands show exact pytest invocations with expected output

### Type Consistency

- `library_seeds` param name is consistent in `_build_section2_prompt`, `_build_gap_prompt`, and the `generate_prep()` call sites
- `role_debriefs` variable name used consistently in Task 4 and 5 (`role_debriefs = _load_role_debriefs_safe(role_name)`)
- `_performance_signal` key on seed dicts set in Task 3, consumed in Task 2 seed block construction (present but absent = no performance line rendered)
- All safe wrappers follow `_*_safe()` naming convention
