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
    write_library,
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

    # -- Introductions ---------------------------------------------------------
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

    # -- Stories ---------------------------------------------------------------
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

    # -- Gap responses ---------------------------------------------------------
    if stage == "recruiter_screen":
        log_lines.append("  INFO: Gap section skipped for recruiter_screen (expected)")
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

    # -- Questions -------------------------------------------------------------
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


def run_backfill(base_dir=WORKSHOPPED_DIR):
    """Discover all .docx files, parse all sections, write library and run log.

    Aborts (does not write library) if >20% of processed entries are duplicates.
    Returns summary dict with keys: files, written, skipped, warnings, log_path, aborted.
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
        f"LIBRARY BACKFILL RUN -- {datetime.now().isoformat()}",
        f"Source dir: {base_dir}",
        f"Files discovered: {len(docx_files)}",
        "=" * 60,
    ]

    for docx_path, role, stage in docx_files:
        stats = _process_file(docx_path, role, stage, library, today, log_lines)
        total_written += stats["written"]
        total_skipped += stats["skipped"]
        all_warnings.extend(stats["warnings"])

    # 20% duplicate guard
    total_candidates = total_written + total_skipped
    dup_ratio = total_skipped / total_candidates if total_candidates > 0 else 0.0
    if dup_ratio > 0.20:
        abort_msg = (
            f"\nSTOP: {dup_ratio:.0%} of entries are duplicates (threshold: 20%).\n"
            "This likely indicates a schema mismatch. Review before proceeding.\n"
            "Library was NOT written."
        )
        print(abort_msg)
        log_lines.extend(["\n" + "=" * 60, "ABORTED -- duplicate ratio exceeded threshold", abort_msg])
        _write_run_log(log_lines, log_path)
        return {
            "files": len(docx_files),
            "written": 0,
            "skipped": total_skipped,
            "warnings": all_warnings,
            "log_path": log_path,
            "aborted": True,
        }

    # Write library
    write_library(library)

    # Write run log
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
