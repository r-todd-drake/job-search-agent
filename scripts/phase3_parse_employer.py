# ==============================================
# phase3_parse_employer.py
# Re-parse a single employer from experience_library.md
# and overwrite only that employer's JSON file.
#
# Usage:
#   python scripts/phase3_parse_employer.py "Employer Name"
#   python scripts/phase3_parse_employer.py "Employer Name" --keywords
#   python scripts/phase3_parse_employer.py "Employer Name" --keywords
#
# Matching: case-insensitive substring — "employer name" matches "Employer Name Inc."
# Keywords are skipped by default. Add --keywords to generate them.
#
# Output:
#   data/experience_library/employers/[name].json
# ==============================================

import os
import sys
import argparse
from anthropic import Anthropic
from dotenv import load_dotenv
from scripts.utils.library_parser import (
    parse_library, add_keywords, save_employers, employer_to_filename
)

load_dotenv()

LIBRARY_PATH = "data/experience_library/experience_library.md"
EMPLOYERS_DIR = "data/experience_library/employers"
KEYWORD_DELAY = 0.5

# ==============================================
# MAIN
# ==============================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Re-parse a single employer from experience_library.md"
    )
    parser.add_argument("employer", help="Employer name or substring to match (case-insensitive)")
    parser.add_argument("--keywords", action="store_true", help="Generate keywords via Claude API")
    args = parser.parse_args()

    print("=" * 60)
    print("PHASE 3 \u2013 SINGLE EMPLOYER PARSER")
    print("=" * 60)

    if not os.path.exists(LIBRARY_PATH):
        print(f"ERROR: Library file not found: {LIBRARY_PATH}")
        sys.exit(1)

    print(f"\nParsing {LIBRARY_PATH}...")
    all_employers, _ = parse_library(LIBRARY_PATH)

    # Case-insensitive substring match
    query = args.employer.lower()
    matches = {name: data for name, data in all_employers.items()
               if query in name.lower()}

    if not matches:
        print(f"\nERROR: No employer matched \"{args.employer}\"")
        print(f"\nKnown employers:")
        for name in all_employers:
            print(f"  {name}")
        sys.exit(1)

    if len(matches) > 1:
        print(f"\nERROR: \"{args.employer}\" matched {len(matches)} employers \u2013 be more specific:")
        for name in matches:
            print(f"  {name}")
        sys.exit(1)

    emp_name, emp_data = next(iter(matches.items()))
    print(f"\nMatched: {emp_name}")

    flag_count = sum(1 for b in emp_data['bullets'] if b['flagged'])
    verify_count = sum(1 for b in emp_data['bullets'] if b['verify'])
    priority_count = sum(1 for b in emp_data['bullets'] if b['priority'])
    print(f"  Bullets: {len(emp_data['bullets'])} "
          f"({flag_count} flagged, {verify_count} verify, {priority_count} priority)")

    if args.keywords:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        add_keywords(matches, [], client, keyword_delay=KEYWORD_DELAY)
    else:
        print("\nKeyword generation skipped (pass --keywords to generate)")

    print(f"\nSaving...")
    os.makedirs(EMPLOYERS_DIR, exist_ok=True)
    filename = employer_to_filename(emp_name)
    filepath = os.path.join(EMPLOYERS_DIR, filename)

    import json
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(emp_data, f, indent=2, ensure_ascii=False)

    print(f"  Saved: {filename}")
    print(f"\n{'=' * 60}")
    print(f"DONE \u2013 {emp_name} re-parsed and saved.")
    print(f"{'=' * 60}")
    print(f"\nReminder: run phase3_compile_library.py to merge into experience_library.json")
