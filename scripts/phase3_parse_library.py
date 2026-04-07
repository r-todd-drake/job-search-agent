# ==============================================
# phase3_parse_library.py
# Full parse of experience_library.md – all employers.
# Writes one JSON file per employer + summaries.json.
#
# Output:
#   data/experience_library/employers/[name].json
#   data/experience_library/summaries.json
#
# Run this once after library updates.
# Then run phase3_compile_library.py to merge.
#
# To re-parse a single employer without a full run:
#   python scripts/phase3_parse_employer.py "employer name"
# ==============================================

import os
from anthropic import Anthropic
from dotenv import load_dotenv
from scripts.utils.library_parser import (
    parse_library, add_keywords, save_employers, save_summaries
)

load_dotenv()

# ==============================================
# CONFIGURATION
# ==============================================

LIBRARY_PATH = "data/experience_library/experience_library.md"
EMPLOYERS_DIR = "data/experience_library/employers"
SUMMARIES_PATH = "data/experience_library/summaries.json"
GENERATE_KEYWORDS = True   # Set False to skip API calls (faster, no keywords)
KEYWORD_DELAY = 0.5        # Seconds between API calls to avoid rate limiting

# ==============================================
# MAIN
# ==============================================

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 3 \u2013 EXPERIENCE LIBRARY PARSER")
    print("=" * 60)

    if not os.path.exists(LIBRARY_PATH):
        print(f"ERROR: Library file not found: {LIBRARY_PATH}")
        exit(1)

    print(f"\nParsing {LIBRARY_PATH}...")
    employers, summaries = parse_library(LIBRARY_PATH)

    print(f"\nParsed:")
    print(f"  Employers: {len(employers)}")
    for name, data in employers.items():
        flag_count = sum(1 for b in data['bullets'] if b['flagged'])
        verify_count = sum(1 for b in data['bullets'] if b['verify'])
        print(f"    {name}: {len(data['bullets'])} bullets "
              f"({flag_count} flagged, {verify_count} verify)")
    print(f"  Summaries: {len(summaries)}")

    if GENERATE_KEYWORDS:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        add_keywords(employers, summaries, client, keyword_delay=KEYWORD_DELAY)
    else:
        print("\nKeyword generation skipped (GENERATE_KEYWORDS=False)")

    print("\nSaving employer files...")
    saved_files = save_employers(employers, EMPLOYERS_DIR)

    print("Saving summaries...")
    save_summaries(summaries, SUMMARIES_PATH)

    print(f"\n{'=' * 60}")
    print(f"PHASE 3 PARSE COMPLETE")
    print(f"  Employer files: {len(saved_files)}")
    print(f"  Summaries: {len(summaries)}")
    print(f"  Output directory: {EMPLOYERS_DIR}")
    print(f"{'=' * 60}")
    print(f"\nNext step: run phase3_compile_library.py to merge into experience_library.json")
