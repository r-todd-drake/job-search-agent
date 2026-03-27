# ==============================================
# phase5_interview_prep.py
# Generates interview preparation materials for
# a specific job application using the Claude API
# and candidate experience library.
#
# Produces three sections in a single output file:
#   1. Company & Role Brief
#   2. Role Analysis, Story Bank & Gap Prep
#   3. Questions to Ask
#
# PII is stripped from all API calls via pii_filter.py
#
# Usage:
#   python scripts/phase5_interview_prep.py --role Viasat_SE_IS
# ==============================================

import os
import sys
import json
import argparse
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv

# Add project root to path for utils import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.pii_filter import strip_pii

load_dotenv()

# ==============================================
# CONFIGURATION
# ==============================================

JOBS_PACKAGES_DIR = "data/job_packages"
CANDIDATE_PROFILE_PATH = "data/experience_library/candidate_profile.md"
EXPERIENCE_LIBRARY = "data/experience_library/experience_library.json"
OUTPUT_FILENAME = "interview_prep.txt"

# ==============================================
# SALARY EXTRACTION
# ==============================================

def extract_salary(jd_text):
    """
    Extract salary range from JD text and estimate offer midpoint.
    Returns dict with range, midpoint, and expectations guidance.
    """
    import re

    # Common salary patterns
    patterns = [
        r'\$\s*([\d,]+(?:\.\d+)?)[kK]?\s*[-–—to]+\s*\$?\s*([\d,]+(?:\.\d+)?)[kK]?',
        r'([\d,]+(?:\.\d+)?)\s*[-–—to]+\s*([\d,]+(?:\.\d+)?)\s*/\s*(?:year|yr|annually)',
    ]

    low = None
    high = None

    for pattern in patterns:
        matches = re.findall(pattern, jd_text, re.IGNORECASE)
        if matches:
            for match in matches:
                try:
                    v1 = float(match[0].replace(',', ''))
                    v2 = float(match[1].replace(',', ''))
                    # Convert k values
                    if v1 < 1000:
                        v1 *= 1000
                    if v2 < 1000:
                        v2 *= 1000
                    # Sanity check — SE salaries 80k-400k range
                    if 80000 <= v1 <= 400000 and 80000 <= v2 <= 400000:
                        low = min(v1, v2)
                        high = max(v1, v2)
                        break
                except:
                    continue
            if low and high:
                break

    if not low or not high:
        return {
            'found': False,
            'text': 'Salary range not found in JD — research market rate before interview',
            'guidance': 'Research Glassdoor, Levels.fyi, and LinkedIn Salary for this role and location.'
        }

    midpoint = (low + high) / 2
    # Realistic offer zone — companies typically start at 50-65% of range
    offer_low = low + (high - low) * 0.45
    offer_high = low + (high - low) * 0.65
    # Anchor recommendation — target 70-80% of range
    anchor = low + (high - low) * 0.72

    return {
        'found': True,
        'low': f"${low:,.0f}",
        'high': f"${high:,.0f}",
        'midpoint': f"${midpoint:,.0f}",
        'offer_zone': f"${offer_low:,.0f} – ${offer_high:,.0f}",
        'anchor': f"${anchor:,.0f}",
        'text': f"${low:,.0f} – ${high:,.0f} (midpoint ${midpoint:,.0f})",
        'guidance': (
            f"Posted range: ${low:,.0f} – ${high:,.0f}\n"
            f"  Realistic offer zone: ${offer_low:,.0f} – ${offer_high:,.0f} "
            f"(companies rarely start at the top)\n"
            f"  Suggested anchor: {f'${anchor:,.0f}'} — positions you above midpoint\n"
            f"  If asked for expectations: '{f'${anchor:,.0f}'} based on my 20+ years of "
            f"defense SE experience and current TS/SCI clearance, though I'm open to "
            f"discussing total compensation.'\n"
            f"  Floor: Do not accept below ${low + (high-low)*0.35:,.0f} for this role level."
        )
    }

# ==============================================
# ARGUMENT PARSING
# ==============================================

parser = argparse.ArgumentParser(description='Phase 5 Interview Prep Generator')
parser.add_argument('--role', type=str, required=True,
                    help='Role package folder name (e.g. Viasat_SE_IS)')
args = parser.parse_args()

ROLE = args.role
PACKAGE_DIR = os.path.join(JOBS_PACKAGES_DIR, ROLE)
JD_PATH = os.path.join(PACKAGE_DIR, "job_description.txt")
OUTPUT_PATH = os.path.join(PACKAGE_DIR, OUTPUT_FILENAME)

# ==============================================
# VALIDATE INPUTS
# ==============================================

print("=" * 60)
print("PHASE 5 — INTERVIEW PREP GENERATOR")
print("=" * 60)
print(f"Role: {ROLE}")
print(f"Package: {PACKAGE_DIR}")

errors = []

if not os.path.exists(PACKAGE_DIR):
    errors.append(f"Job package folder not found: {PACKAGE_DIR}")
if not os.path.exists(JD_PATH):
    errors.append(f"job_description.txt not found in {PACKAGE_DIR}")
if not os.path.exists(CANDIDATE_PROFILE_PATH):
    errors.append(f"candidate_profile.md not found: {CANDIDATE_PROFILE_PATH}")
if not os.path.exists(EXPERIENCE_LIBRARY):
    errors.append(f"experience_library.json not found: {EXPERIENCE_LIBRARY}")

if errors:
    print("\nERRORS — cannot proceed:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)

# ==============================================
# LOAD DATA
# ==============================================

print("\nLoading data...")

with open(JD_PATH, encoding='utf-8') as f:
    jd = f.read()

with open(CANDIDATE_PROFILE_PATH, encoding='utf-8') as f:
    raw_profile = f.read()

# Strip PII before any API call
candidate_profile = strip_pii(raw_profile)
print("  Candidate profile loaded and PII stripped.")

# Extract salary from JD
salary_data = extract_salary(jd)
if salary_data['found']:
    print(f"  Salary range found: {salary_data['text']}")
else:
    print(f"  Salary range: not found in JD")

with open(EXPERIENCE_LIBRARY, encoding='utf-8') as f:
    library = json.load(f)

# Build a concise bullet summary from the library for context
# Top 5 bullets per employer, max 3 employers for token efficiency
def build_library_summary(library, max_employers=4, bullets_per_employer=5):
    summary = []
    for employer in library['employers']:
        name = employer['name']
        bullets = [b for b in employer['bullets'] if not b.get('flagged')][:bullets_per_employer]
        if bullets:
            summary.append(f"\n{name}:")
            for b in bullets:
                summary.append(f"  - {b['text'][:150]}")
    return "\n".join(summary)

library_summary = build_library_summary(library)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ==============================================
# SYSTEM PROMPT
# ==============================================

SYSTEM_PROMPT = """You are an expert career coach specializing in defense and aerospace
systems engineering. You help senior engineers prepare for technical interviews with
defense prime contractors and technology companies.

You always:
- Provide specific, actionable guidance grounded in the candidate's actual background
- Frame stories using the STAR format (Situation, Task, Action, Result)
- Give honest gap assessments with confident, truthful talking points
- Tailor questions to demonstrate genuine domain knowledge
- Keep language professional and direct

You never:
- Invent experience the candidate does not have
- Suggest the candidate claim skills or credentials they lack
- Use vague or generic interview advice
- Use em dashes (use en dashes instead)"""

# ==============================================
# SECTION 1 — COMPANY & ROLE BRIEF
# ==============================================

print("\nGenerating Section 1: Company & Role Brief...")

company_prompt = """Generate a concise company and role brief for interview preparation.

JOB DESCRIPTION:
__JD_TEXT__

Provide the following in this exact format:

COMPANY OVERVIEW:
[3-4 sentences on the company — what they do, their defense/government focus,
relevant business units, scale and reputation in the defense market]

INTEGRATED SOLUTIONS BUSINESS UNIT:
[2-3 sentences specifically about the business unit hiring for this role —
what they work on, their customer base, their technical focus]

ROLE IN CONTEXT:
[2-3 sentences on what this role actually does day-to-day based on the JD —
the "glue" framing, what success looks like in this position]

SALARY & LEVEL CONTEXT:
JD posted range: __SALARY_TEXT__
[1-2 sentences on what level this salary band represents and where
in the range a realistic initial offer is likely to land]

SALARY EXPECTATIONS GUIDANCE:
__SALARY_GUIDANCE__

KEY TALKING POINTS ABOUT THE COMPANY:
[3 bullet points — things to mention that show you researched the company
and understand their mission. Keep these factual and grounded.]

RECENT CONTEXT TO BE AWARE OF:
[1-2 sentences on anything relevant about Viasat's current business
situation, programs, or direction that might come up in conversation.
Note if you are uncertain about recency of information.]"""

# Format salary info for prompt
salary_text = salary_data['text'] if salary_data['found'] else 'Not found in JD'
salary_guidance = salary_data['guidance'] if salary_data['found'] else 'Research market rate before interview'
company_prompt = (company_prompt
    .replace('__SALARY_TEXT__', salary_text)
    .replace('__SALARY_GUIDANCE__', salary_guidance)
    .replace('__JD_TEXT__', jd[:3000]))

response1 = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1000,
    system=SYSTEM_PROMPT,
    messages=[{"role": "user", "content": company_prompt}]
)
section1 = response1.content[0].text

# ==============================================
# SECTION 2 — ROLE ANALYSIS, STORY BANK & GAP PREP
# ==============================================

print("Generating Section 2: Role Analysis, Story Bank & Gap Prep...")

story_prompt = f"""Generate interview preparation materials for this specific role.

CANDIDATE PROFILE (PII removed):
{candidate_profile[:4000]}

SAMPLE BULLETS FROM EXPERIENCE LIBRARY:
{library_summary[:2000]}

JOB DESCRIPTION:
{jd[:3000]}

Provide the following in this exact format:

ROLE FIT ASSESSMENT:
[3-4 sentences on overall fit — where the candidate is strongest and
where there are genuine gaps. Be honest.]

KEY THEMES TO LEAD WITH:
[3 themes with 1-2 sentences each — the strongest narratives to emphasize
throughout the interview based on JD requirements]

STORY BANK — STAR FORMAT:
[Generate 5 interview stories in STAR format, each mapped to a specific
JD requirement. Label each with the JD theme it addresses.]

STORY 1 — [JD Theme]:
Situation: [context]
Task: [what needed to be done]
Action: [what the candidate did specifically]
Result: [outcome — no fabricated metrics, frame qualitatively if needed]

STORY 2 — [JD Theme]:
[same format]

STORY 3 — [JD Theme]:
[same format]

STORY 4 — [JD Theme]:
[same format]

STORY 5 — [JD Theme]:
[same format]

GAP PREPARATION:
[For each significant gap between JD requirements and candidate background,
provide an honest, confident talking point. Do not suggest claiming
experience the candidate does not have.]

GAP 1 — [Topic]:
Honest answer: [what to say]
Bridge: [how to connect to relevant actual experience]

GAP 2 — [Topic]:
Honest answer: [what to say]
Bridge: [how to connect to relevant actual experience]

GAP 3 — [Topic]:
Honest answer: [what to say]
Bridge: [how to connect to relevant actual experience]

LIKELY INTERVIEW QUESTIONS:
[List 8 questions likely to be asked based on this JD and role level,
with a brief note on how to approach each]"""

response2 = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=3000,
    system=SYSTEM_PROMPT,
    messages=[{"role": "user", "content": story_prompt}]
)
section2 = response2.content[0].text

# ==============================================
# SECTION 3 — QUESTIONS TO ASK
# ==============================================

print("Generating Section 3: Questions to Ask...")

questions_prompt = f"""Generate thoughtful questions for a candidate to ask during
a 45-minute phone interview for this role.

JOB DESCRIPTION:
{jd[:2000]}

CANDIDATE BACKGROUND SUMMARY:
Senior Systems Engineer, 20+ years defense experience, MBSE expertise,
Project Overmatch (CNO priority program) MBSE Pillar Lead, autonomous systems
(UAS and maritime), C4ISR, V-model, requirements analysis specialist.
Current TS/SCI clearance.

Generate 8 questions organized into three categories. Each question should
demonstrate domain knowledge and genuine curiosity — not generic interview questions.

Format exactly as:

QUESTIONS ABOUT THE ROLE & TEAM:
1. [Question] — [Why ask this / what it signals]
2. [Question] — [Why ask this / what it signals]
3. [Question] — [Why ask this / what it signals]

QUESTIONS ABOUT THE PROGRAM & TECHNICAL ENVIRONMENT:
4. [Question] — [Why ask this / what it signals]
5. [Question] — [Why ask this / what it signals]
6. [Question] — [Why ask this / what it signals]

QUESTIONS ABOUT SUCCESS & GROWTH:
7. [Question] — [Why ask this / what it signals]
8. [Question] — [Why ask this / what it signals]

CLOSING NOTE:
[1-2 sentences on how to close the interview — what to leave them with]"""

response3 = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1200,
    system=SYSTEM_PROMPT,
    messages=[{"role": "user", "content": questions_prompt}]
)
section3 = response3.content[0].text

# ==============================================
# COMPILE AND SAVE OUTPUT
# ==============================================

print("\nCompiling output...")

output_lines = []
output_lines.append("=" * 60)
output_lines.append("INTERVIEW PREP PACKAGE")
output_lines.append("=" * 60)
output_lines.append(f"Role: {ROLE}")
output_lines.append(f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")
output_lines.append("Note: PII stripped from all API calls.")
output_lines.append("=" * 60)
output_lines.append("")

output_lines.append("SECTION 1 — COMPANY & ROLE BRIEF")
output_lines.append("-" * 60)
output_lines.append(section1)
output_lines.append("")

output_lines.append("=" * 60)
output_lines.append("SECTION 2 — ROLE ANALYSIS, STORY BANK & GAP PREP")
output_lines.append("-" * 60)
output_lines.append(section2)
output_lines.append("")

output_lines.append("=" * 60)
output_lines.append("SECTION 3 — QUESTIONS TO ASK")
output_lines.append("-" * 60)
output_lines.append(section3)
output_lines.append("")

output_lines.append("=" * 60)
output_lines.append("END OF INTERVIEW PREP PACKAGE")
output_lines.append(f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")
output_lines.append("=" * 60)

output_text = "\n".join(output_lines)

# Check if file already exists
if os.path.exists(OUTPUT_PATH):
    print(f"\nWARNING: {OUTPUT_FILENAME} already exists in {PACKAGE_DIR}")
    response = input("  Overwrite? (y/n): ").strip().lower()
    if response != 'y':
        print("  Cancelled. Existing file preserved.")
        sys.exit(0)

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(output_text)

print(f"\n{'=' * 60}")
print("PHASE 5 COMPLETE")
print(f"{'=' * 60}")
print(f"Output saved: {OUTPUT_PATH}")
print(f"\nNext steps:")
print(f"  1. Open {OUTPUT_PATH} in VS Code")
print(f"  2. Review company brief for accuracy")
print(f"  3. Practice STAR stories out loud")
print(f"  4. Select 4-5 questions to ask from Section 3")
print(f"  5. Note any gap prep talking points to rehearse")
print(f"{'=' * 60}")
