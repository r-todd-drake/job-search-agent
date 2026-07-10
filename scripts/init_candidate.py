# scripts/init_candidate.py
# Guided terminal wizard for populating context/candidate/candidate_config.yaml.
#
# Usage:
#   python -m scripts.init_candidate

import os
import sys
import yaml
from pathlib import Path

from scripts.utils import candidate_config as _cc

_CONFIG_PATH = Path("context/candidate/candidate_config.yaml")
_EXAMPLE_PATH = Path("context/candidate/candidate_config.example.yaml")


def collect_education():
    """Prompt for education fields. Returns dict."""
    print("\n--- Section 1: Education ---")

    degrees = []
    while True:
        institution = input("Institution name (required): ").strip()
        if not institution:
            print("Institution name is required.")
            continue
        degree = input("Degree name (required): ").strip()
        if not degree:
            print("Degree name is required.")
            continue
        notes = input("Notes (optional — press Enter to skip): ").strip()
        degrees.append({"institution": institution, "degree": degree, "notes": notes})
        if input("Add another degree? (y/n): ").strip().lower() != "y":
            break

    continuing_education = []
    print("\nContinuing education (press Enter to skip):")
    while True:
        institution = input("Institution (or press Enter to finish): ").strip()
        if not institution:
            break
        program = input("Program name: ").strip()
        status = input("Status (enrolled/completed): ").strip()
        continuing_education.append({"institution": institution, "program": program,
                                      "status": status})

    not_held_labels = []
    print("\nDegree types you do NOT hold that are commonly assumed (press Enter when done):")
    while True:
        label = input("  > ").strip()
        if not label:
            break
        not_held_labels.append(label)

    return {
        "degrees": degrees,
        "continuing_education": continuing_education,
        "not_held_labels": not_held_labels,
    }


def collect_certifications():
    """Prompt for certifications. Returns dict with active, lapsed, not_held."""
    print("\n--- Section 2: Certifications ---")

    active = []
    print("Active certifications (press Enter when done):")
    while True:
        cert = input("  > ").strip()
        if not cert:
            break
        active.append(cert)

    lapsed = []
    print("Lapsed certifications (once held, no longer current — press Enter when done):")
    while True:
        cert = input("  > ").strip()
        if not cert:
            break
        lapsed.append(cert)

    not_held = []
    print("Certifications you do NOT hold that interviewers commonly ask about "
          "(press Enter when done):")
    while True:
        cert = input("  > ").strip()
        if not cert:
            break
        not_held.append(cert)

    return {"active": active, "lapsed": lapsed, "not_held": not_held}


def collect_military():
    """Prompt for military service. Returns dict."""
    print("\n--- Section 3: Military Service (optional) ---")
    if input("Do you have military service to include? (y/n, or press Enter to skip): "
             ).strip().lower() != "y":
        return {"service": []}

    service = []
    while True:
        branch = input("Branch of service: ").strip()
        mos = input("MOS/rate/specialty: ").strip()
        dates = input("Service dates (e.g., 1991–1994): ").strip()
        notes = input("Notes (optional — press Enter to skip): ").strip()
        service.append({"branch": branch, "mos": mos, "dates": dates, "notes": notes})
        if input("Add another service period? (y/n): ").strip().lower() != "y":
            break

    return {"service": service}


def collect_clearance():
    """Prompt for security clearance. Returns dict (empty if none)."""
    print("\n--- Section 4: Security Clearance (optional) ---")
    if input("Do you hold or have you held a security clearance? (y/n, or press Enter to skip): "
             ).strip().lower() != "y":
        return {}

    level = input("Clearance level (e.g., TS/SCI, Secret, Public Trust): ").strip()
    status = input("Status — 'Current' (between employers) or 'Active' (on a program): ").strip()
    granted = input("Year granted: ").strip()

    return {"level": level, "status": status, "granted": granted}


def collect_skills():
    """Prompt for skills. Returns dict with programming, tools, not_held."""
    print("\n--- Section 5: Skills ---")

    programming = input(
        "Describe your programming and scripting background in a sentence or two:\n  > "
    ).strip()

    tools = []
    print("Specific tools you use (press Enter when done):")
    while True:
        tool = input("  > ").strip()
        if not tool:
            break
        tools.append(tool)

    not_held = []
    print("Tools or skills you do NOT have that interviewers commonly ask about "
          "(press Enter when done):")
    while True:
        item = input("  > ").strip()
        if not item:
            break
        not_held.append(item)

    return {"programming": programming, "tools": tools, "not_held": not_held}


def collect_gaps():
    """Prompt for confirmed experience gaps. Returns list of strings."""
    print("\n--- Section 6: Confirmed Gaps ---")
    print("List any known experience gaps — things hiring managers ask about that "
          "you cannot fully claim.")
    print("Write each as a complete sentence. Press Enter twice when done.")

    gaps = []
    while True:
        gap = input("  > ").strip()
        if not gap:
            break
        gaps.append(gap)

    return gaps


def collect_employers():
    """Prompt for employers in reverse chronological order. Returns list of dicts."""
    print("\n--- Section 7: Employers ---")
    print("List employers in reverse chronological order (most recent first).")
    print("Tier 1 = most recent/primary, Tier 2 = secondary, Tier 3 = oldest/brief stints.")
    print("Names must match exactly what appears in your experience_library.json.")

    employers = []
    while True:
        name = input("Exact employer name: ").strip()
        while True:
            tier_str = input("Tier (1/2/3): ").strip()
            if tier_str in ("1", "2", "3"):
                break
            print("Enter 1, 2, or 3.")
        employers.append({"name": name, "tier": int(tier_str)})
        if input("Add another employer? (y/n): ").strip().lower() != "y":
            break

    return employers


def collect_resume_defaults():
    """Prompt for resume header defaults. Returns dict."""
    print("\n--- Section 8: Resume Defaults ---")
    role_title = input(
        "Your role title as it should appear on your resume\n"
        "  (e.g., 'Senior Systems Engineer'): "
    ).strip()
    education_line = input(
        "Education line for resume footer\n"
        "  (e.g., 'State University — B.S. Engineering'): "
    ).strip()
    certifications_line = input(
        "Certifications line for resume footer\n"
        "  (e.g., 'ICAgile Certified Professional | Current TS/SCI'): "
    ).strip()
    return {
        "role_title": role_title,
        "education_line": education_line,
        "certifications_line": certifications_line,
    }


def collect_style_rules():
    """Prompt for style rules. Returns dict."""
    print("\n--- Section 9: Style Rules ---")
    terminology = []
    if input("Do you have terms to flag if they appear on your resume? (y/n): "
             ).strip().lower() == "y":
        print("For each term: provide the pattern to flag, the replacement, "
              "and whether the check is case-sensitive.")
        while True:
            pattern = input("  Pattern to flag: ").strip()
            if not pattern:
                break
            replacement = input("  Replacement to suggest: ").strip()
            case_sensitive = input("  Case-sensitive? (y/n): ").strip().lower() == "y"
            rule_name = pattern[:40]
            terminology.append({
                "rule_name": rule_name,
                "pattern": pattern,
                "replacement": replacement,
                "case_sensitive": case_sensitive,
            })
            if input("  Add another? (y/n): ").strip().lower() != "y":
                break

    return {
        "dash_style": "en dash only — never em dash",
        "metric_rule": "no unverifiable metrics",
        "terminology": terminology,
    }


def run_wizard():
    """Drive the full 10-section wizard and save candidate_config.yaml."""
    print("\n=== Candidate Setup Wizard ===")
    print("This wizard will help you set up your candidate profile.")
    print(f"Your answers are saved to {_CONFIG_PATH} (private — never committed to git).")
    print("Press Ctrl+C at any time to cancel without saving.\n")

    # Handle existing config
    if _CONFIG_PATH.exists():
        print(f"WARNING: {_CONFIG_PATH} already exists.")
        choice = input(
            "Options:\n"
            "  [e] Edit existing file (re-run wizard with current values)\n"
            "  [o] Overwrite — start fresh (requires confirmation)\n"
            "  [c] Cancel\n"
            "Enter choice (e/o/c): "
        ).strip().lower()
        if choice == "c" or not choice:
            print("Cancelled. No changes made.")
            sys.exit(0)
        if choice == "o":
            confirm = input("Type 'yes' to confirm overwrite: ").strip()
            if confirm.lower() != "yes":
                print("Cancelled. No changes made.")
                sys.exit(0)

    education_data = collect_education()
    certs_data = collect_certifications()
    military_data = collect_military()
    clearance_data = collect_clearance()
    skills_data = collect_skills()
    gaps_data = collect_gaps()
    employers_data = collect_employers()
    resume_defaults_data = collect_resume_defaults()
    style_rules_data = collect_style_rules()

    print(
        "\n--- Section 10: Intro Monologue ---\n"
        "The intro_monologue and short_tenure_explanation fields require your own voice\n"
        "and cannot be generated here. Placeholder text will be written to the config.\n"
        "Open context/candidate/candidate_config.yaml in a text editor and fill them in\n"
        "before running Phase 5 interview prep."
    )

    data = {
        "education": education_data,
        "certifications": certs_data,
        "military": military_data,
        "clearance": clearance_data,
        "confirmed_skills": skills_data,
        "confirmed_gaps": gaps_data,
        "employers": employers_data,
        "resume_defaults": resume_defaults_data,
        "style_rules": style_rules_data,
        "intro_monologue": "[placeholder — fill in manually]",
        "short_tenure_explanation": "[placeholder — fill in manually if applicable]",
    }

    save_config(data, config_path=_CONFIG_PATH)

    print(
        f"\nSetup complete. Saved to {_CONFIG_PATH}\n\n"
        "Next steps:\n"
        "  1. Fill in intro_monologue and short_tenure_explanation in the config file.\n"
        "  2. If you haven't already, build your experience library:\n"
        "     - Create data/experience_library/experience_library.md with your work history\n"
        "     - Run: python -m scripts.phase3_parse_library\n"
        "     - Run: python -m scripts.phase3_build_candidate_profile\n"
        "     - Run: python -m scripts.phase3_compile_library\n"
        "  3. Confirm setup is complete:\n"
        "     - python -m scripts.phase2_job_ranking\n"
        "     - python -m scripts.phase2_semantic_analyzer\n"
        "  4. If you haven't set your domain config, copy the example:\n"
        "     context/domain/domain_config.example.yaml → context/domain/domain_config.yaml\n"
        "     Fill in domain_label before running Phase 2, 4, 5, or 6."
    )


def save_config(data, config_path=_CONFIG_PATH):
    """Write wizard data to candidate_config.yaml and validate with the loader."""
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)

    # Validate: point the loader at the written file, reload, then restore
    original_path = _cc._CONFIG_PATH
    _cc._CONFIG_PATH = str(config_path)
    _cc._config = None
    try:
        _cc.load()  # raises yaml.YAMLError or FileNotFoundError if the write failed
    finally:
        _cc._CONFIG_PATH = original_path
        _cc._config = None


def main():
    if not _EXAMPLE_PATH.exists():
        print(
            f"ERROR: {_EXAMPLE_PATH} not found.\n"
            "The example template is missing — the repository may be incomplete.\n"
            "Clone the repo again or check your installation."
        )
        sys.exit(1)

    run_wizard()


if __name__ == "__main__":
    main()
