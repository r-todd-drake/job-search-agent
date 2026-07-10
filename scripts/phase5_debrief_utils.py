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
