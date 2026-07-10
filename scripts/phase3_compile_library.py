import os
import json
from datetime import datetime
from scripts.config import EXPERIENCE_LIBRARY_JSON as OUTPUT_PATH
from scripts.utils import candidate_config


EMPLOYERS_DIR = "data/experience_library/employers"
SUMMARIES_PATH = "data/experience_library/summaries.json"


def compile_library(employers_dir, summaries_path, chrono_order=None):
    """
    Load all employer JSON files and summaries, merge into a single library dict.
    Employers are ordered by CHRONOLOGICAL_ORDER from candidate_config.yaml (or the
    chrono_order list if supplied directly — used by tests to inject fixture names).
    Files whose name field is not in CHRONOLOGICAL_ORDER are skipped with a warning.
    Returns the compiled library dict (does not write to disk).
    """
    if chrono_order is None:
        chrono_order = [e["name"] for e in candidate_config.load().get("employers", [])]

    employer_files = [f for f in os.listdir(employers_dir) if f.endswith('.json')]

    employers_by_name = {}
    total_bullets = total_flagged = total_verify = 0

    for filename in sorted(employer_files):
        filepath = os.path.join(employers_dir, filename)
        with open(filepath, encoding='utf-8') as f:
            emp_data = json.load(f)
        name = emp_data.get('name', '')
        if name not in chrono_order:
            print(f"  WARNING: {filename} has name '{name}' not in CHRONOLOGICAL_ORDER — skipping")
            continue
        employers_by_name[name] = emp_data
        total_bullets += len(emp_data.get('bullets', []))
        total_flagged += sum(1 for b in emp_data.get('bullets', []) if b.get('flagged'))
        total_verify += sum(1 for b in emp_data.get('bullets', []) if b.get('verify'))

    for name in chrono_order:
        if name not in employers_by_name:
            print(f"  WARNING: '{name}' in CHRONOLOGICAL_ORDER but no matching employer file found")

    employers = [employers_by_name[name] for name in chrono_order if name in employers_by_name]

    summaries_data = {"total": 0, "summaries": []}
    if os.path.exists(summaries_path):
        with open(summaries_path, encoding='utf-8') as f:
            summaries_data = json.load(f)

    return {
        "metadata": {
            "last_compiled": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_employers": len(employers),
            "total_bullets": total_bullets,
            "total_flagged": total_flagged,
            "total_verify": total_verify,
            "total_summaries": summaries_data.get('total', 0),
            "employer_names": [e['name'] for e in employers]
        },
        "employers": employers,
        "summaries": summaries_data.get('summaries', [])
    }


def main():
    print("=" * 60)
    print("PHASE 3 - COMPILE EXPERIENCE LIBRARY")
    print("=" * 60)

    if not os.path.exists(EMPLOYERS_DIR):
        print(f"ERROR: Employers directory not found: {EMPLOYERS_DIR}")
        print("Run phase3_parse_library.py first.")
        exit(1)

    employer_files = [f for f in os.listdir(EMPLOYERS_DIR) if f.endswith('.json')]
    if not employer_files:
        print(f"ERROR: No employer JSON files found in {EMPLOYERS_DIR}")
        exit(1)

    print(f"\nLoading {len(employer_files)} employer files...")
    library = compile_library(EMPLOYERS_DIR, SUMMARIES_PATH)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(library, f, indent=2, ensure_ascii=False)

    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"\nCOMPILE COMPLETE")
    print(f"  Output: {OUTPUT_PATH}")
    print(f"  File size: {size_kb:.1f} KB")
    print(f"  Employers: {library['metadata']['total_employers']}")
    print(f"  Total bullets: {library['metadata']['total_bullets']}")
    print(f"  Summaries: {library['metadata']['total_summaries']}")
    print(f"\nLibrary ready for Phase 4 resume generator.")


if __name__ == "__main__":
    main()
