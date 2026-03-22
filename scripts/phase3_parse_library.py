# ==============================================
# phase3_parse_library.py
# Parses experience_library.md into structured
# JSON files — one per employer plus a summaries
# file. Calls Claude API to generate keywords
# for each bullet (semantic keyword extraction).
#
# Output:
#   data/experience_library/employers/[name].json
#   data/experience_library/summaries.json
#
# Run this once after library updates.
# Then run phase3_compile_library.py to merge.
# ==============================================

import os
import re
import json
import time
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# ==============================================
# CONFIGURATION
# ==============================================

LIBRARY_PATH = "data/experience_library/experience_library.md"
EMPLOYERS_DIR = "data/experience_library/employers"
SUMMARIES_PATH = "data/experience_library/summaries.json"
GENERATE_KEYWORDS = False   # Set False to skip API calls (faster, no keywords)
KEYWORD_DELAY = 0.5        # Seconds between API calls to avoid rate limiting

# ==============================================
# HELPERS
# ==============================================

def clean_theme_name(raw):
    """Strip (new from tranche X) and similar suffixes from theme names."""
    return re.sub(r'\s*\(new from tranche \d+\)', '', raw).strip()

def clean_bullet_text(raw):
    """Remove [FLAGGED] and [VERIFY] tags from bullet text for storage."""
    return raw.replace('[FLAGGED]', '').replace('[VERIFY]', '').strip()

def is_flagged(text):
    return '[FLAGGED]' in text

def is_verify(text):
    return '[VERIFY]' in text

def employer_to_filename(name):
    """Convert employer name to safe filename."""
    safe = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    safe = safe.strip().lower().replace(' ', '_')
    # Truncate if too long
    return safe[:40] + '.json'

def get_keywords(client, bullet_text):
    """Call Claude API to extract keywords from a bullet."""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": f"""Extract 5-8 keywords from this resume bullet that a hiring manager 
or ATS system would search for. Return ONLY a JSON array of lowercase strings, 
no explanation, no markdown formatting.

Bullet: {bullet_text}"""
            }]
        )
        raw = response.content[0].text.strip()
        # Clean any accidental markdown
        raw = raw.replace('```json', '').replace('```', '').strip()
        keywords = json.loads(raw)
        return [k.lower() for k in keywords if isinstance(k, str)]
    except Exception as e:
        print(f"    WARNING: Keyword generation failed — {str(e)[:60]}")
        return []

# ==============================================
# PARSE LIBRARY
# ==============================================

def parse_library(filepath):
    """
    Parse experience_library.md into structured data.
    Returns: (employers dict, summaries list)
    """
    with open(filepath, encoding='utf-8') as f:
        lines = f.readlines()

    employers = {}       # employer_name -> employer dict
    summaries = []       # list of summary dicts
    current_employer = None
    current_theme = None
    current_bullet = None
    in_summaries = False
    current_summary_theme = None

    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\n')
        stripped = line.strip()

        # Skip comment lines and dividers
        # Must check ## and ### BEFORE single # — otherwise headers get eaten by comment rule
        if stripped == '---' or stripped == '':
            i += 1
            continue
        if stripped.startswith('#') and not stripped.startswith('##'):
            i += 1
            continue

        # Detect summaries section
        if stripped.startswith('## PROFESSIONAL SUMMARIES'):
            in_summaries = True
            current_employer = None
            current_theme = None
            current_bullet = None
            i += 1
            continue

        # ── SUMMARIES SECTION ──────────────────────────────────────────
        if in_summaries:
            # Summary theme heading
            if stripped.startswith('### '):
                current_summary_theme = stripped[4:].strip()
                i += 1
                continue

            # Summary text (quoted)
            if stripped.startswith('"') and current_summary_theme:
                summary_text = stripped.strip('"')
                # Check if summary continues on next lines
                while not stripped.endswith('"') and i + 1 < len(lines):
                    i += 1
                    stripped = lines[i].strip()
                    summary_text += ' ' + stripped.strip('"')

                # Get source from next *Used in* line
                sources = []
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('*Used in:'):
                        src_text = next_line.replace('*Used in:', '').replace('*', '').strip()
                        sources = [s.strip() for s in src_text.split(',')]
                        i += 1

                summaries.append({
                    "id": f"summary_{len(summaries) + 1:03d}",
                    "theme": current_summary_theme,
                    "text": summary_text.strip(),
                    "sources": sources,
                    "keywords": [],
                    "flagged": False
                })
                i += 1
                continue

            i += 1
            continue

        # ── EMPLOYERS SECTION ──────────────────────────────────────────

        # Employer heading (## NAME)
        if stripped.startswith('## ') and not stripped.startswith('## PROFESSIONAL'):
            # Save any pending bullet
            if current_bullet and current_employer:
                employers[current_employer]['bullets'].append(current_bullet)
                current_bullet = None

            employer_name = stripped[3:].strip()
            current_employer = employer_name
            current_theme = None

            if employer_name not in employers:
                employers[employer_name] = {
                    "name": employer_name,
                    "short_name": employer_name.split('(')[0].strip(),
                    "title": "",
                    "dates": "",
                    "domain": "",
                    "standing_rules": [],
                    "bullets": []
                }
            i += 1
            continue

        # Employer metadata
        if stripped.startswith('**Title:**') and current_employer:
            employers[current_employer]['title'] = stripped.replace('**Title:**', '').strip()
            i += 1
            continue

        if stripped.startswith('**Dates:**') and current_employer:
            employers[current_employer]['dates'] = stripped.replace('**Dates:**', '').strip()
            i += 1
            continue

        if stripped.startswith('**Domain:**') and current_employer:
            employers[current_employer]['domain'] = stripped.replace('**Domain:**', '').strip()
            i += 1
            continue

        # Standing rules
        if stripped.startswith('>') and current_employer:
            rule_text = stripped.lstrip('>').strip()
            if rule_text:
                employers[current_employer]['standing_rules'].append(rule_text)
            i += 1
            continue

        # Theme heading
        if stripped.startswith('### ') and current_employer:
            # Save pending bullet
            if current_bullet:
                employers[current_employer]['bullets'].append(current_bullet)
                current_bullet = None

            raw_theme = stripped[4:].strip()
            # Remove "Theme: " prefix if present
            if raw_theme.startswith('Theme:'):
                raw_theme = raw_theme[6:].strip()
            current_theme = clean_theme_name(raw_theme)
            i += 1
            continue

        # Bullet line
        if stripped.startswith('- ') and current_employer and current_theme:
            # Save previous bullet
            if current_bullet:
                employers[current_employer]['bullets'].append(current_bullet)

            bullet_raw = stripped[2:].strip()
            current_bullet = {
                "id": "",  # assigned later
                "theme": current_theme,
                "keywords": [],
                "text": clean_bullet_text(bullet_raw),
                "sources": [],
                "notes": [],
                "flagged": is_flagged(bullet_raw),
                "verify": is_verify(bullet_raw)
            }
            i += 1
            continue

        # Source attribution line
        if stripped.startswith('*Used in:') and current_bullet:
            src_text = stripped.replace('*Used in:', '').replace('*', '').strip()
            current_bullet['sources'] = [s.strip() for s in src_text.split(',')]
            i += 1
            continue

        # Note line
        if stripped.startswith('*NOTE:') and current_bullet:
            note_text = stripped.replace('*NOTE:', '').replace('*', '').strip()
            current_bullet['notes'].append(note_text)
            i += 1
            continue

        i += 1

    # Save any final pending bullet
    if current_bullet and current_employer:
        employers[current_employer]['bullets'].append(current_bullet)

    # Assign bullet IDs
    for emp_name, emp_data in employers.items():
        prefix = re.sub(r'[^a-z]', '', emp_name.lower())[:6]
        for idx, b in enumerate(emp_data['bullets']):
            b['id'] = f"{prefix}_{idx + 1:03d}"

    return employers, summaries

# ==============================================
# GENERATE KEYWORDS
# ==============================================

def add_keywords(employers, summaries, client):
    """Call Claude API to generate keywords for all bullets and summaries."""

    total_bullets = sum(len(e['bullets']) for e in employers.values())
    total_summaries = len(summaries)
    processed = 0

    print(f"\nGenerating keywords for {total_bullets} bullets and {total_summaries} summaries...")
    print(f"Estimated API cost: ~${(total_bullets + total_summaries) * 0.0003:.2f}\n")

    for emp_name, emp_data in employers.items():
        print(f"  {emp_name} ({len(emp_data['bullets'])} bullets)...")
        for bullet in emp_data['bullets']:
            if bullet['flagged']:
                bullet['keywords'] = []  # Don't generate for flagged bullets
                continue
            bullet['keywords'] = get_keywords(client, bullet['text'])
            processed += 1
            if processed % 10 == 0:
                print(f"    {processed}/{total_bullets} bullets processed...")
            time.sleep(KEYWORD_DELAY)

    print(f"  Summaries ({total_summaries})...")
    for summary in summaries:
        summary['keywords'] = get_keywords(client, summary['text'])
        time.sleep(KEYWORD_DELAY)

    print(f"  Keywords complete.")

# ==============================================
# SAVE OUTPUT
# ==============================================

def save_employers(employers, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    saved = []
    for emp_name, emp_data in employers.items():
        filename = employer_to_filename(emp_name)
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(emp_data, f, indent=2, ensure_ascii=False)
        saved.append(filename)
        print(f"  Saved: {filename} ({len(emp_data['bullets'])} bullets)")

    return saved

def save_summaries(summaries, filepath):
    data = {
        "total": len(summaries),
        "summaries": summaries
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved: summaries.json ({len(summaries)} summaries)")

# ==============================================
# MAIN
# ==============================================

print("=" * 60)
print("PHASE 3 — EXPERIENCE LIBRARY PARSER")
print("=" * 60)

# Check library file exists
if not os.path.exists(LIBRARY_PATH):
    print(f"ERROR: Library file not found: {LIBRARY_PATH}")
    exit(1)

# Parse the library
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

# Generate keywords via Claude API
if GENERATE_KEYWORDS:
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    add_keywords(employers, summaries, client)
else:
    print("\nKeyword generation skipped (GENERATE_KEYWORDS=False)")

# Save output
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
