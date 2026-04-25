# ==============================================
# phase3_build_candidate_profile.py
# Builds a canonical candidate profile from the
# experience library. Reads each employer section
# and asks Claude to extract confirmed facts,
# skills, tools, and explicit gaps. Compiles
# everything into a single candidate_profile.md
# for use by Phase 4 resume generator.
#
# Run once after library is built or updated.
# Output: data/experience_library/candidate_profile.md
#
# Usage:
#   python -m scripts.phase3_build_candidate_profile
# ==============================================

import os
import json
import time
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
from scripts.utils.pii_filter import strip_pii
from scripts.config import (
    EXPERIENCE_LIBRARY_JSON as LIBRARY_JSON,
    CANDIDATE_PROFILE_PATH as OUTPUT_PATH,
    MODEL_SONNET,
)
from scripts.utils import candidate_config

load_dotenv()

# ==============================================
# CONFIGURATION
# ==============================================

EMPLOYERS_DIR = "data/experience_library/employers"
SUMMARIES_PATH = "data/experience_library/summaries.json"
API_DELAY = 0.5  # seconds between calls

SYSTEM_PROMPT = """You are building a canonical candidate profile from resume experience data.
Your job is to extract ONLY confirmed facts - skills, tools, roles, and scope that are
explicitly demonstrated in the provided bullets.

You NEVER invent, infer, or embellish. If a skill is not explicitly demonstrated in the
bullets, it does not appear in the profile. If something is ambiguous, note it as
"familiarity" or "exposure" rather than claiming expertise.

Your output will be used to prevent AI hallucinations when generating future resumes.
Accuracy and explicit gap documentation are more important than completeness."""


# ==============================================
# CORE FUNCTION
# ==============================================

def build_profile(client, library_json_path, output_path):
    """
    Build a canonical candidate profile from the experience library.

    Args:
        client: Anthropic client instance
        library_json_path: Path to experience_library.json
        output_path: Path for the output candidate_profile.md
    """
    with open(library_json_path, encoding='utf-8') as f:
        library = json.load(f)

    # Load summaries – prefer inline in library, fall back to summaries.json
    summaries_raw = library.get('summaries', [])
    if not summaries_raw:
        summaries_path = os.path.join(
            os.path.dirname(library_json_path), 'summaries.json'
        )
        if os.path.exists(summaries_path):
            with open(summaries_path, encoding='utf-8') as f:
                summaries_data = json.load(f)
            summaries_raw = summaries_data.get('summaries', [])

    employer_profiles = {}

    # ==============================================
    # STEP 1 – EXTRACT PER-EMPLOYER PROFILE
    # ==============================================

    print(f"\nStep 1: Extracting confirmed skills per employer...")

    for employer in library['employers']:
        name = employer['name']
        title = employer.get('title', '')
        dates = employer.get('dates', '')
        bullets = [b for b in employer['bullets'] if not b.get('flagged')]

        if not bullets:
            print(f"  Skipping {name} – no cleared bullets")
            continue

        print(f"  Processing {name} ({len(bullets)} bullets)...")

        # Build bullet text block
        bullet_text = "\n".join([f"- {b['text']}" for b in bullets])

        prompt = f"""Analyze these resume bullets for {name} ({title}, {dates}) and extract
a confirmed skills and capabilities profile.

BULLETS:
{bullet_text}

Extract and return in this EXACT format:

EMPLOYER: {name}
TITLE: {title}
DATES: {dates}

CONFIRMED TOOLS AND TECHNOLOGIES:
[List only tools explicitly named in the bullets - one per line with brief evidence]

CONFIRMED TECHNICAL SKILLS:
[List only skills explicitly demonstrated - one per line]

CONFIRMED LEADERSHIP AND SCOPE:
[Team sizes, program scope, stakeholder levels explicitly mentioned]

CONFIRMED DOMAIN KNOWLEDGE:
[Mission areas, platforms, programs explicitly referenced]

KEY BULLETS (top 3 most impactful for senior SE roles):
[Copy the 3 strongest bullets verbatim]

GAPS VISIBLE FROM THIS ROLE:
[Note any skills commonly expected for this role type that are NOT demonstrated in these bullets]

Be conservative. Only list what is explicitly demonstrated, not what can be inferred."""

        safe_prompt = strip_pii(prompt)

        try:
            response = client.messages.create(
                model=MODEL_SONNET,
                max_tokens=1500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": safe_prompt}]
            )
            employer_profiles[name] = response.content[0].text
            print(f"    Done.")
        except Exception as e:
            print(f"    ERROR: {str(e)[:80]}")
            employer_profiles[name] = f"ERROR processing {name}: {str(e)}"

        time.sleep(API_DELAY)

    # ==============================================
    # STEP 2 – EXTRACT SUMMARY THEMES
    # ==============================================

    print(f"\nStep 2: Analyzing summary themes...")

    summary_themes = []
    for s in summaries_raw:
        summary_themes.append(f"- {s['theme']}: {s['text'][:150]}...")

    summary_block = "\n".join(summary_themes[:20])  # First 20 for context

    summary_prompt = f"""Analyze these resume summary themes and identify the consistent
positioning patterns and core value propositions across all versions.

SUMMARY THEMES:
{summary_block}

Return:
CONSISTENT POSITIONING THEMES:
[3-5 themes that appear consistently across summaries]

STRONGEST VALUE PROPOSITIONS:
[The 2-3 most powerful and differentiated claims that appear across summaries]

POSITIONING TO AVOID:
[Any themes that appear overclaimed or inconsistent with a systems engineering background]"""

    safe_summary_prompt = strip_pii(summary_prompt)

    try:
        response = client.messages.create(
            model=MODEL_SONNET,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": safe_summary_prompt}]
        )
        summary_analysis = response.content[0].text
        print("  Done.")
    except Exception as e:
        summary_analysis = f"ERROR: {str(e)}"
        print(f"  ERROR: {str(e)[:80]}")

    # ==============================================
    # STEP 3 – COMPILE MASTER PROFILE
    # ==============================================

    print(f"\nStep 3: Compiling master candidate profile...")

    # Build compilation input
    employer_summaries = ""
    for name, profile in employer_profiles.items():
        employer_summaries += f"\n\n{'='*40}\n{profile}\n"

    compile_prompt = f"""You are compiling a master canonical candidate profile for use in
resume generation. This profile will be used to PREVENT hallucinations – it defines
exactly what the candidate has and has NOT done.

EMPLOYER PROFILES EXTRACTED FROM LIBRARY:
{employer_summaries}

SUMMARY ANALYSIS:
{summary_analysis}

CONFIRMED SUPPLEMENTAL FACTS:
{candidate_config.build_known_facts()}

Compile a comprehensive master profile in this format:

# CANONICAL CANDIDATE PROFILE
# [CANDIDATE] - Compiled from Experience Library
# Generated: {datetime.now().strftime('%d %b %Y')}
# PURPOSE: Use this file to ground all resume generation - prevents hallucinations

## IDENTITY & CONTACT
[name, location, contact, clearance]

## EDUCATION & CERTIFICATIONS
[confirmed education and certs - include explicit statement of what is NOT held]

## MILITARY SERVICE
[confirmed service history]

## CAREER SUMMARY
[2-3 sentence overview grounded in confirmed experience]

## SIGNATURE CREDENTIAL
[Project Overmatch - confirmed details only]

## CONFIRMED SKILLS BY CATEGORY

### MBSE & Architecture Tools
[tools confirmed in library - note proficiency level where distinguishable]

### Systems Engineering Skills
[confirmed SE capabilities]

### Domain Knowledge
[confirmed mission areas and platforms]

### Leadership & Stakeholder Management
[confirmed leadership scope]

### Technical Writing & Documentation
[confirmed documentation capabilities]

## EMPLOYER HISTORY
[each employer with confirmed title, dates, key capabilities - 3-4 bullets each]

## CONFIRMED GAPS - NEVER INCLUDE ON RESUME
[explicit list of skills, tools, certifications the candidate does NOT have]
[This section is critical for preventing hallucinations]

## STYLE RULES
[formatting and content rules for all resume output]

## CANONICAL BULLETS - HIGHEST IMPACT
[Top 5-7 bullets across all employers that should be prioritized]

Be thorough on the CONFIRMED GAPS section - it is the most important part of this document."""

    safe_compile_prompt = strip_pii(compile_prompt)

    try:
        response = client.messages.create(
            model=MODEL_SONNET,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": safe_compile_prompt}]
        )
        master_profile = response.content[0].text
        print("  Done.")
    except Exception as e:
        master_profile = f"ERROR compiling master profile: {str(e)}"
        print(f"  ERROR: {str(e)[:80]}")

    # ==============================================
    # STEP 4 – SAVE OUTPUT
    # ==============================================

    print(f"\nStep 4: Saving candidate profile...")

    candidate_name = os.getenv('CANDIDATE_NAME', '[CANDIDATE]')
    total_bullets = library.get('metadata', {}).get('total_bullets', 0)
    total_employers = library.get('metadata', {}).get('total_employers', 0)

    header = f"""# CANONICAL CANDIDATE PROFILE
# {candidate_name}
# Generated: {datetime.now().strftime('%d %b %Y %H:%M')}
# Source: experience_library.json ({total_bullets} bullets,
#         {total_employers} employers)
#
# PURPOSE: Ground all Phase 4 resume generation - prevents hallucinations
# USAGE: Load this file into CANDIDATE_PROFILE in phase4_resume_generator.py
#        Replace the hardcoded CANDIDATE_PROFILE constant with the contents of this file
#
# HIERARCHY: PROJECT_CONTEXT.md governs over this file where conflicts exist.
# ==============================================

"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True) if os.path.dirname(output_path) else None

    cfg = candidate_config.load()
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(master_profile)
        f.write(f"\n\n## INTRO MONOLOGUE\n{cfg['intro_monologue']}\n")
        f.write(f"\n\n## SHORT TENURE EXPLANATION\n{cfg['short_tenure_explanation']}\n")

    size_kb = os.path.getsize(output_path) / 1024

    print(f"\n{'=' * 60}")
    print(f"CANDIDATE PROFILE BUILD COMPLETE")
    print(f"  Output: {output_path}")
    print(f"  File size: {size_kb:.1f} KB")
    print(f"\nNext steps:")
    print(f"  1. Review {output_path} in VS Code")
    print(f"  2. Update CANDIDATE_PROFILE in phase4_resume_generator.py")
    print(f"     to load from this file instead of the hardcoded constant")
    print(f"  3. Rerun Stage 1 to verify improved hallucination prevention")
    print(f"{'=' * 60}")


# ==============================================
# ENTRY POINT
# ==============================================

def main():
    print("=" * 60)
    print("PHASE 3 – BUILD CANDIDATE PROFILE")
    print("=" * 60)

    if not os.path.exists(LIBRARY_JSON):
        print(f"ERROR: {LIBRARY_JSON} not found. Run phase3_compile_library.py first.")
        exit(1)

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    build_profile(client, LIBRARY_JSON, OUTPUT_PATH)


if __name__ == "__main__":
    main()
