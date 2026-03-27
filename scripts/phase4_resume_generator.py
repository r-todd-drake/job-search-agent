# ==============================================
# phase4_resume_generator.py
# AI-powered resume tailoring pipeline.
# Four-stage asynchronous workflow:
#
# Stage 1: Keyword + semantic bullet selection
#          Reads JD, queries experience library,
#          outputs stage1_draft.txt for review
#
# Stage 2: Manual review (no script needed)
#          Edit stage1_draft.txt in VS Code
#          Save as stage2_approved.txt
#
# Stage 3: Semantic review + wording suggestions
#          Reads stage2_approved.txt + JD,
#          outputs stage3_review.txt
#
# Stage 4: Document generation
#          Reads stage4_final.txt (or stage2_approved.txt),
#          generates .docx + runs check_resume.py
#
# Usage:
#   python scripts/phase4_resume_generator.py --stage 1 --role BAH_LCI_MBSE
#   python scripts/phase4_resume_generator.py --stage 3 --role BAH_LCI_MBSE
#   python scripts/phase4_resume_generator.py --stage 4 --role BAH_LCI_MBSE
# ==============================================

import os
import re
import json
import argparse
import hashlib
import subprocess
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
from docx import Document as DocxDocument
from docx.shared import Pt
from docx.oxml.ns import qn
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
import docx

load_dotenv()

# ==============================================
# CONFIGURATION
# ==============================================

JOBS_PACKAGES_DIR = "data/job_packages"
EXPERIENCE_LIBRARY = "data/experience_library/experience_library.json"
CANDIDATE_PROFILE_PATH = "data/experience_library/candidate_profile.md"
RESUME_TEMPLATE = "templates/resume_template.docx"
RESUMES_TAILORED_DIR = "resumes/tailored"
CHECK_RESUME_SCRIPT = "scripts/check_resume.py"

# Employer tier definitions — controls bullet priority and trimming order
EMPLOYER_TIERS = {
    "SARONIC TECHNOLOGIES": 1,
    "KFORCE (Supporting Leidos / NIWC PAC)": 1,
    "SHIELD AI": 1,
    "G2 OPS": 1,
    "SAIC": 2,
    "L3 COMMUNICATIONS": 3,
    "U.S. ARMY": 3,
}

# Max candidate bullets per employer sent to semantic selection
# More candidates = better selection but higher API cost
MAX_CANDIDATES_TIER1 = 12
MAX_CANDIDATES_TIER2 = 6
MAX_CANDIDATES_TIER3 = 4

# Load canonical candidate profile dynamically
# This replaces the hardcoded profile and prevents hallucinations
def load_candidate_profile():
    if os.path.exists(CANDIDATE_PROFILE_PATH):
        with open(CANDIDATE_PROFILE_PATH, encoding='utf-8') as f:
            return f.read()
    else:
        print(f"WARNING: candidate_profile.md not found at {CANDIDATE_PROFILE_PATH}")
        print("  Run phase3_build_candidate_profile.py to generate it.")
        print("  Using fallback minimal profile.")
        return """
CANDIDATE: R. Todd Drake
CLEARANCE: Current TS/SCI
LOCATION: San Diego, CA
EXPERIENCE: 20+ years defense systems engineering
EDUCATION: B.A. Geography, GIS & Remote Sensing (NOT Systems Engineering)
GAPS: No GitLab, no Terraform, no INCOSE, no FAA/DO-178, no FEA/CFD
RULES: En dashes only, no unverifiable metrics, Saronic = maritime only
"""

CANDIDATE_PROFILE = load_candidate_profile()

# ==============================================
# ARGUMENT PARSING
# ==============================================

parser = argparse.ArgumentParser(description='Phase 4 Resume Generator')
parser.add_argument('--stage', type=int, required=True, choices=[1, 3, 4],
                    help='Stage to run (1, 3, or 4)')
parser.add_argument('--role', type=str, required=True,
                    help='Role package folder name (e.g. BAH_LCI_MBSE)')
args = parser.parse_args()

ROLE = args.role
STAGE = args.stage
PACKAGE_DIR = os.path.join(JOBS_PACKAGES_DIR, ROLE)
RESUME_OUTPUT_DIR = os.path.join(RESUMES_TAILORED_DIR, ROLE)

# File paths
JD_PATH = os.path.join(PACKAGE_DIR, "job_description.txt")
STAGE1_PATH = os.path.join(PACKAGE_DIR, "stage1_draft.txt")
STAGE2_PATH = os.path.join(PACKAGE_DIR, "stage2_approved.txt")
STAGE3_PATH = os.path.join(PACKAGE_DIR, "stage3_review.txt")
STAGE4_PATH = os.path.join(PACKAGE_DIR, "stage4_final.txt")

# ==============================================
# VALIDATION HELPERS
# ==============================================

def validate_inputs(stage):
    """Validate required files exist before running a stage."""
    errors = []

    # Always required
    if not os.path.exists(PACKAGE_DIR):
        errors.append(
            f"Job package folder not found: {PACKAGE_DIR}\n"
            f"  Create the folder and add job_description.txt before running Stage 1."
        )
        return errors  # No point checking further

    if not os.path.exists(JD_PATH):
        errors.append(
            f"job_description.txt not found in {PACKAGE_DIR}\n"
            f"  Paste the full job description into {JD_PATH} before running Stage 1."
        )

    if not os.path.exists(EXPERIENCE_LIBRARY):
        errors.append(
            f"experience_library.json not found: {EXPERIENCE_LIBRARY}\n"
            f"  Run phase3_compile_library.py to generate it."
        )

    if stage >= 3:
        if not os.path.exists(STAGE2_PATH):
            errors.append(
                f"stage2_approved.txt not found in {PACKAGE_DIR}\n"
                f"  Review {STAGE1_PATH} in VS Code, make your edits,\n"
                f"  and save as stage2_approved.txt before running Stage 3."
            )
        elif os.path.exists(STAGE1_PATH):
            # Warn if stage2 appears to be unedited copy of stage1
            with open(STAGE1_PATH) as f:
                s1_hash = hashlib.md5(f.read().encode()).hexdigest()
            with open(STAGE2_PATH) as f:
                s2_hash = hashlib.md5(f.read().encode()).hexdigest()
            if s1_hash == s2_hash:
                errors.append(
                    f"WARNING: stage2_approved.txt appears identical to stage1_draft.txt.\n"
                    f"  Did you forget to review and edit stage1_draft.txt?\n"
                    f"  If you intentionally approved without changes, rename to continue."
                )

    if stage == 4:
        # Use stage4_final.txt if it exists, otherwise fall back to stage2_approved.txt
        if not os.path.exists(STAGE4_PATH) and not os.path.exists(STAGE2_PATH):
            errors.append(
                f"Neither stage4_final.txt nor stage2_approved.txt found in {PACKAGE_DIR}\n"
                f"  Complete Stage 2 review before running Stage 4."
            )

    return errors

def check_overwrite(filepath, stage_name):
    """Warn if output file already exists."""
    if os.path.exists(filepath):
        print(f"\nWARNING: {stage_name} output already exists: {filepath}")
        response = input("  Overwrite? (y/n): ").strip().lower()
        if response != 'y':
            print("  Cancelled. Existing file preserved.")
            return False
    return True

# ==============================================
# LOAD DATA
# ==============================================

def load_jd():
    with open(JD_PATH, encoding='utf-8') as f:
        return f.read()

def load_library():
    with open(EXPERIENCE_LIBRARY, encoding='utf-8') as f:
        return json.load(f)

def load_text(filepath):
    with open(filepath, encoding='utf-8') as f:
        return f.read()

# ==============================================
# STAGE 1 — BULLET SELECTION
# ==============================================

def keyword_score_bullet(bullet, jd_lower):
    """Score a bullet based on keyword overlap with JD."""
    if not bullet.get('keywords'):
        return 0
    score = 0
    for kw in bullet['keywords']:
        if kw.lower() in jd_lower:
            score += 1
    return score

def stage1_select_bullets(client, jd, library):
    """
    Stage 1: Keyword pre-filter + semantic selection.
    Returns structured draft content.
    """
    print("\nStage 1: Selecting bullets from experience library...")
    jd_lower = jd.lower()

    # Step 1A — Keyword pre-filter per employer
    candidates_by_employer = {}
    for employer in library['employers']:
        name = employer['name']
        tier = EMPLOYER_TIERS.get(name, 2)
        max_candidates = {1: MAX_CANDIDATES_TIER1,
                         2: MAX_CANDIDATES_TIER2,
                         3: MAX_CANDIDATES_TIER3}.get(tier, 6)

        # Score and sort bullets
        scored = []
        for bullet in employer['bullets']:
            if bullet.get('flagged'):
                continue
            score = keyword_score_bullet(bullet, jd_lower)
            scored.append((score, bullet))

        scored.sort(key=lambda x: -x[0])
        top = [b for score, b in scored[:max_candidates] if score > 0 or len(scored) <= max_candidates]

        # Always include at least some bullets for Tier 1 employers
        if tier == 1 and len(top) == 0:
            top = [b for _, b in scored[:3]]

        if top:
            candidates_by_employer[name] = {
                'tier': tier,
                'bullets': top
            }

    print(f"  Keyword pre-filter: {sum(len(v['bullets']) for v in candidates_by_employer.values())} candidate bullets across {len(candidates_by_employer)} employers")

    # Step 1B — Semantic selection via Claude API
    print("  Running semantic selection...")

    candidates_text = ""
    for emp_name, data in candidates_by_employer.items():
        candidates_text += f"\n## {emp_name} (Tier {data['tier']})\n"
        for i, bullet in enumerate(data['bullets'], 1):
            candidates_text += f"  [{i}] {bullet['text']}\n"
            candidates_text += f"      Theme: {bullet['theme']}\n"

    # Select summaries
    summaries_text = ""
    for i, s in enumerate(library['summaries'], 1):
        summaries_text += f"[{i}] Theme: {s['theme']}\n{s['text'][:200]}...\n\n"

    prompt = f"""You are selecting resume content for a job application.

CANDIDATE PROFILE:
{CANDIDATE_PROFILE}

JOB DESCRIPTION:
{jd[:3000]}

CANDIDATE BULLETS BY EMPLOYER (pre-filtered by keyword relevance):
{candidates_text}

AVAILABLE SUMMARIES:
{summaries_text}

INSTRUCTIONS:
1. Select the best bullets for each employer based on fit with this specific JD.
   - Tier 1 employers (Saronic, KForce, Shield AI, G2 OPS): select 3-5 bullets each
   - Tier 2 employers (SAIC): select 1-3 bullets if relevant, 0 if not
   - Tier 3 employers (L3, Army): select 0-1 bullets only if directly relevant
   - If an employer has low relevance, select fewer or no bullets
   - DEDUPLICATION: Never select two bullets from the same employer that cover
     substantially the same topic or use similar language. If two bullets make
     the same point, select only the stronger, more specific one.
   
2. Select the best matching summary (by number), or flag if none are a strong fit.

3. Return your response in EXACTLY this format:

SUMMARY_SELECTION: [number or "NONE — suggest new"]
SUMMARY_REASON: [one sentence why]

EMPLOYER: [exact employer name]
BULLETS_SELECTED: [comma-separated bullet numbers]
SELECTION_REASON: [one sentence rationale]

EMPLOYER: [next employer]
...

Do not include any other text. Follow the format exactly."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    selection_text = response.content[0].text

    # Step 1C — Generate core competencies
    print("  Generating core competencies...")
    comp_prompt = f"""You are generating a Core Competencies section for a defense systems engineering resume.

CANDIDATE PROFILE:
{CANDIDATE_PROFILE}

JOB DESCRIPTION:
{jd[:2000]}

Generate 5-7 core competency bullet lines for this specific role.
Each line should follow this format: "Category: specific skill 1, specific skill 2, specific skill 3"

Rules:
- Only include competencies the candidate genuinely has based on the profile above
- Mirror JD language where accurate
- Always include a Clearance & Certifications line last
- The Clearance & Certifications line must be EXACTLY:
  "Clearance & Certifications: Current TS/SCI | ICAgile Certified Professional"
- CRITICAL: The candidate's actual degree is B.A. Geography, GIS & Remote Sensing — NOT Systems Engineering
  Never claim a degree the candidate does not hold
- Never invent experience, credentials, or education not in the candidate profile
- NEVER include these specific tools the candidate does not have:
  GitLab, Terraform, INCOSE certification, FAA/DO-178, FEA, CFD, Cucumber, TDD
- Version control experience is GitHub only — never GitLab
- If a JD requires a tool the candidate lacks, omit it entirely from competencies
- En dashes only, never em dashes

Return ONLY the competency lines, one per line, no numbering, no extra text."""

    comp_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": comp_prompt}]
    )
    competencies = comp_response.content[0].text.strip()

    # Step 1D — Parse selections and build draft
    draft = build_stage1_draft(jd, selection_text, candidates_by_employer,
                                library['summaries'], library, competencies)
    return draft

def build_stage1_draft(jd, selection_text, candidates_by_employer,
                        summaries, library, competencies=""):
    """Parse Claude's selection response and build the stage1 draft."""

    lines = selection_text.strip().split('\n')
    draft_lines = []

    # Header
    draft_lines.append("=" * 60)
    draft_lines.append("STAGE 1 DRAFT — FOR YOUR REVIEW")
    draft_lines.append("=" * 60)
    draft_lines.append(f"Role: {ROLE}")
    draft_lines.append(f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")
    draft_lines.append("")
    draft_lines.append("INSTRUCTIONS:")
    draft_lines.append("  1. Review selected summary and bullets below")
    draft_lines.append("  2. Swap, add, or remove bullets as needed")
    draft_lines.append("  3. Adjust wording if desired")
    draft_lines.append("  4. Save this file as stage2_approved.txt when satisfied")
    draft_lines.append("  5. Run Stage 3 for semantic review before generating .docx")
    draft_lines.append("=" * 60)
    draft_lines.append("")

    # Parse summary selection
    summary_num = None
    summary_reason = ""
    current_employer = None
    employer_bullets = {}
    employer_reasons = {}

    for line in lines:
        line = line.strip()
        if line.startswith("SUMMARY_SELECTION:"):
            val = line.replace("SUMMARY_SELECTION:", "").strip()
            if "NONE" in val.upper():
                summary_num = None
            else:
                try:
                    summary_num = int(re.search(r'\d+', val).group())
                except:
                    summary_num = None
        elif line.startswith("SUMMARY_REASON:"):
            summary_reason = line.replace("SUMMARY_REASON:", "").strip()
        elif line.startswith("EMPLOYER:"):
            current_employer = line.replace("EMPLOYER:", "").strip()
            employer_bullets[current_employer] = []
        elif line.startswith("BULLETS_SELECTED:") and current_employer:
            nums_str = line.replace("BULLETS_SELECTED:", "").strip()
            try:
                nums = [int(n.strip()) for n in nums_str.split(',') if n.strip().isdigit()]
                employer_bullets[current_employer] = nums
            except:
                pass
        elif line.startswith("SELECTION_REASON:") and current_employer:
            employer_reasons[current_employer] = line.replace("SELECTION_REASON:", "").strip()

    # Write summary section
    draft_lines.append("## PROFESSIONAL SUMMARY")
    draft_lines.append("")
    if summary_num and summary_num <= len(summaries):
        selected_summary = summaries[summary_num - 1]
        draft_lines.append(f"[Source: Summary #{summary_num} — {selected_summary['theme']}]")
        draft_lines.append(f"[Reason: {summary_reason}]")
        draft_lines.append("")
        draft_lines.append(selected_summary['text'])
    else:
        draft_lines.append("[FLAG: No strong summary match found in library.]")
        draft_lines.append("[A suggested summary will be generated in Stage 3.]")
        draft_lines.append("[Placeholder — replace with approved summary text]")
    draft_lines.append("")

    # Write core competencies section
    draft_lines.append("## CORE COMPETENCIES")
    draft_lines.append("")
    if competencies:
        for line in competencies.split("\n"):
            line = line.strip()
            if line:
                draft_lines.append(f"- {line}")
    else:
        draft_lines.append("[No competencies generated — add manually]")
    draft_lines.append("")

    # Write employer sections in reverse chronological order
    CHRONOLOGICAL_ORDER = [
        "SARONIC TECHNOLOGIES",
        "KFORCE (Supporting Leidos / NIWC PAC)",
        "SHIELD AI",
        "G2 OPS",
        "SAIC",
        "L3 COMMUNICATIONS",
        "U.S. ARMY",
    ]
    tier_order = sorted(
        candidates_by_employer.keys(),
        key=lambda x: CHRONOLOGICAL_ORDER.index(x) if x in CHRONOLOGICAL_ORDER else 99
    )

    for emp_name in tier_order:
        data = candidates_by_employer[emp_name]
        selected_nums = employer_bullets.get(emp_name, [])
        reason = employer_reasons.get(emp_name, "")

        # Get employer metadata
        emp_data = next((e for e in library['employers'] if e['name'] == emp_name), {})
        title = emp_data.get('title', '')
        dates = emp_data.get('dates', '')

        draft_lines.append(f"## {emp_name}")
        if title:
            draft_lines.append(f"Title: {title}")
        if dates:
            draft_lines.append(f"Dates: {dates}")
        if reason:
            draft_lines.append(f"[Selection rationale: {reason}]")
        draft_lines.append("")

        if not selected_nums:
            draft_lines.append("[No bullets selected — remove this section or add manually]")
        else:
            bullets = data['bullets']
            for num in selected_nums:
                if 1 <= num <= len(bullets):
                    bullet = bullets[num - 1]
                    draft_lines.append(f"- {bullet['text']}")
                    draft_lines.append(f"  [Source: {', '.join(bullet['sources'][:2])}]")
                    draft_lines.append(f"  [Theme: {bullet['theme']}]")
                    draft_lines.append("")

        draft_lines.append("")

    # Footer
    draft_lines.append("=" * 60)
    draft_lines.append("END OF STAGE 1 DRAFT")
    draft_lines.append("Save as stage2_approved.txt when ready for Stage 3.")
    draft_lines.append("=" * 60)

    return "\n".join(draft_lines)

# ==============================================
# STAGE 3 — SEMANTIC REVIEW
# ==============================================

def stage3_semantic_review(client, jd, approved_content):
    """
    Stage 3: Semantic review of approved draft.
    Returns advisory report with suggestions.
    """
    print("\nStage 3: Running semantic review...")

    prompt = f"""You are reviewing a draft resume for a specific job application.
Your role is ADVISORY ONLY — suggest improvements, do not rewrite.

CANDIDATE PROFILE AND RULES:
{CANDIDATE_PROFILE}

JOB DESCRIPTION:
{jd[:3000]}

APPROVED RESUME DRAFT:
{approved_content}

Please provide your review in EXACTLY this format:

NARRATIVE COHERENCE:
[Does the summary claim align with the bullets selected? Are there coverage gaps?
Flag any mismatches between what the summary promises and what the bullets prove.]

COVERAGE GAPS:
[List any JD requirements not addressed by the current bullet selection.
For each gap, suggest whether a bullet exists that could fill it or if it should be acknowledged as a gap.]

WORDING SUGGESTIONS:
[For each suggested change, use this format:
ORIGINAL: [exact current text]
SUGGESTED: [proposed revision]
REASON: [why this improves fit, readability, or ATS alignment]
RULE CHECK: [confirm suggestion does not violate any candidate rules]

Only suggest changes grounded in confirmed candidate background.
Flag any suggestion that would require information not in the approved draft.]

ATS KEYWORDS:
[List JD keywords not currently appearing in the draft that could be
naturally incorporated without fabricating experience.]

SUMMARY ASSESSMENT:
[If the draft contains a library summary: confirm it is the best fit or suggest an alternative.
If the draft contains a placeholder: generate a suggested summary based on the selected bullets
and the style of existing summaries. Flag clearly as AI-GENERATED for Todd's review.]

OVERALL ASSESSMENT:
[1-2 sentences on overall fit and readiness for Stage 4.]"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    review_text = response.content[0].text

    # Wrap in header
    output = []
    output.append("=" * 60)
    output.append("STAGE 3 SEMANTIC REVIEW — ADVISORY ONLY")
    output.append("=" * 60)
    output.append(f"Role: {ROLE}")
    output.append(f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")
    output.append("")
    output.append("INSTRUCTIONS:")
    output.append("  1. Review suggestions below")
    output.append("  2. Accept or reject each suggestion in stage2_approved.txt")
    output.append("  3. Save final approved content as stage4_final.txt")
    output.append("  4. Run Stage 4 to generate .docx")
    output.append("=" * 60)
    output.append("")
    output.append(review_text)
    output.append("")
    output.append("=" * 60)
    output.append("END OF STAGE 3 REVIEW")
    output.append("=" * 60)

    return "\n".join(output)

# ==============================================
# STAGE 4 — DOCUMENT GENERATION
# ==============================================

def stage4_generate_docx(final_content, role):
    """
    Stage 4: Parse final approved content and generate .docx resume.
    Uses python-docx with established resume formatting.
    """
    print("\nStage 4: Generating resume document...")

    os.makedirs(RESUME_OUTPUT_DIR, exist_ok=True)

    # Parse the final content into sections
    sections = parse_final_content(final_content)

    # Generate filename
    output_filename = f"{role}_Resume.docx"
    output_path = os.path.join(RESUME_OUTPUT_DIR, output_filename)

    # Build document
    build_docx(sections, output_path)

    return output_path

def parse_final_content(content):
    """Parse stage4_final.txt into structured sections for docx generation."""
    sections = {
        'summary': '',
        'competencies': [],
        'employers': []
    }

    current_section = None
    current_employer = None
    current_bullets = []
    current_title = ''
    current_dates = ''

    lines = content.split('\n')

    for line in lines:
        stripped = line.strip()

        # Skip header/footer lines
        if stripped.startswith('=') or stripped.startswith('STAGE') or \
           stripped.startswith('Role:') or stripped.startswith('Generated:') or \
           stripped.startswith('INSTRUCTIONS:') or stripped.startswith('  ') and \
           current_section is None:
            continue

        # Section detection
        if stripped == '## PROFESSIONAL SUMMARY':
            current_section = 'summary'
            continue

        if stripped == '## CORE COMPETENCIES':
            current_section = 'competencies'
            continue

        if stripped.startswith('## ') and stripped not in ['## PROFESSIONAL SUMMARY', '## CORE COMPETENCIES']:
            # Save previous employer
            if current_employer:
                sections['employers'].append({
                    'name': current_employer,
                    'title': current_title,
                    'dates': current_dates,
                    'bullets': [b for b in current_bullets if b]
                })

            current_employer = stripped[3:].strip()
            current_title = ''
            current_dates = ''
            current_bullets = []
            current_section = 'employer'
            continue

        # Content parsing
        if current_section == 'summary':
            # Skip source/reason tags
            if stripped.startswith('[') and stripped.endswith(']'):
                continue
            if stripped and not stripped.startswith('['):
                sections['summary'] += (' ' if sections['summary'] else '') + stripped

        elif current_section == 'competencies':
            if stripped.startswith('- ') and not stripped.startswith('['):
                comp_text = stripped[2:].strip()
                if comp_text and not comp_text.startswith('['):
                    sections['competencies'].append(comp_text)

        elif current_section == 'employer':
            if stripped.startswith('Title:'):
                current_title = re.sub(r'\[.*?\]', '', stripped.replace('Title:', '')).strip()
            elif stripped.startswith('Dates:'):
                current_dates = re.sub(r'\[.*?\]', '', stripped.replace('Dates:', '')).strip()
            elif stripped.startswith('- ') and not stripped.startswith('['):
                # Extract bullet text only, skip source/theme lines
                bullet_text = stripped[2:].strip()
                if bullet_text and not bullet_text.startswith('['):
                    # Strip any [VERIFY] or [FLAGGED] tags that leaked from library
                    bullet_text = re.sub(r'\s*\[VERIFY[^\]]*\]', '', bullet_text).strip()
                    bullet_text = re.sub(r'\s*\[FLAGGED[^\]]*\]', '', bullet_text).strip()
                    if bullet_text:
                        current_bullets.append(bullet_text)
            # Skip [Source:], [Theme:], [Selection rationale:] lines

    # Save final employer
    if current_employer:
        sections['employers'].append({
            'name': current_employer,
            'title': current_title,
            'dates': current_dates,
            'bullets': [b for b in current_bullets if b]
        })

    return sections

def build_docx(sections, output_path):
    """
    Build the .docx file using the resume template.
    Opens resume_template.docx which contains all custom styles
    (Title, Heading 1, Heading 3, List Bullet, Strong) with
    Aptos font and color scheme already defined.
    Falls back to basic formatting if template not found.
    """
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    # Load template or fall back to blank document
    if os.path.exists(RESUME_TEMPLATE):
        doc = Document(RESUME_TEMPLATE)
        print(f"  Using template: {RESUME_TEMPLATE}")
    else:
        print(f"  WARNING: Template not found at {RESUME_TEMPLATE}")
        print(f"  Save a blank styled document as {RESUME_TEMPLATE}")
        print(f"  Falling back to basic formatting...")
        doc = Document()

    def add_paragraph(text, style='Normal', space_before=0, space_after=4):
        p = doc.add_paragraph(style=style)
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        return p

    def add_name_header():
        # Name — Title style
        p = add_paragraph('', style='Title', space_after=0)
        run = p.add_run("R. Todd Drake")

        # Role title — Heading 1 style
        p2 = add_paragraph('', style='Heading 1', space_after=0)
        run2 = p2.add_run("Senior Systems Engineer")

        # Contact line — Normal 10pt
        p3 = add_paragraph('', style='Normal', space_after=6)
        run3 = p3.add_run(
            "San Diego, CA | (619) 379-5783 | r_todd_d@msn.com | "
            "linkedin.com/in/rtodddrake | github.com/r-todd-drake"
        )
        run3.font.size = Pt(10)

    def add_section_heading(text):
        p = add_paragraph('', style='Heading 1', space_before=8, space_after=2)
        p.add_run(text)

    def add_employer_heading(name, title, dates):
        # Employer – Location on one line as Heading 3
        p = add_paragraph('', style='Heading 3', space_before=6, space_after=0)
        p.add_run(name)

        # Role title (Strong) | Dates (Normal) on one line
        p2 = add_paragraph('', style='Normal', space_before=0, space_after=2)
        if title:
            run1 = p2.add_run(title)
            run1.bold = True
            run1.font.color.rgb = RGBColor(0x17, 0x36, 0x5D)
        if dates:
            run2 = p2.add_run(f"  |  {dates}")
            run2.bold = False

    def add_bullet(text):
        p = add_paragraph('', style='List Bullet', space_after=2)
        p.add_run(text)

    def add_normal(text, size=11):
        p = add_paragraph('', style='Normal', space_after=4)
        run = p.add_run(text)
        run.font.size = Pt(size)

    # Build document content
    add_name_header()

    # Professional Summary
    if sections['summary']:
        add_section_heading("Professional Summary")
        add_normal(sections['summary'])

    # Core Competencies
    if sections.get('competencies'):
        add_section_heading("Core Competencies")
        for comp in sections['competencies']:
            add_bullet(comp)

    # Professional Experience
    if sections['employers']:
        add_section_heading("Professional Experience")
        for emp in sections['employers']:
            if not emp['bullets']:
                continue
            add_employer_heading(emp['name'], emp['title'], emp['dates'])
            for bullet_text in emp['bullets']:
                add_bullet(bullet_text)

    # Earlier Career — if any Tier 3 employers with bullets
    # (handled as regular employers in current implementation)

    # Education & Certifications
    add_section_heading("Education & Certifications")
    add_normal("San Diego State University – B.A. Geography, GIS & Remote Sensing | Army ROTC")
    add_normal("ICAgile Certified Professional | Current TS/SCI")

    doc.save(output_path)
    print(f"  Document saved: {output_path}")

# ==============================================
# MAIN
# ==============================================

print("=" * 60)
print(f"PHASE 4 — RESUME GENERATOR — STAGE {STAGE}")
print("=" * 60)
print(f"Role: {ROLE}")
print(f"Package: {PACKAGE_DIR}")

# Validate inputs
errors = validate_inputs(STAGE)
if errors:
    print("\nERRORS — cannot proceed:")
    for error in errors:
        print(f"\n  {error}")
    exit(1)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── STAGE 1 ──────────────────────────────────────────────────────────────────
if STAGE == 1:
    if not check_overwrite(STAGE1_PATH, "Stage 1 draft"):
        exit(0)

    jd = load_jd()
    library = load_library()

    draft = stage1_select_bullets(client, jd, library)

    with open(STAGE1_PATH, 'w', encoding='utf-8') as f:
        f.write(draft)

    print(f"\nStage 1 complete.")
    print(f"  Draft saved: {STAGE1_PATH}")
    print(f"\nNext steps:")
    print(f"  1. Open {STAGE1_PATH} in VS Code")
    print(f"  2. Review selected bullets and summary")
    print(f"  3. Make any edits")
    print(f"  4. Save as {STAGE2_PATH}")
    print(f"  5. Run: python scripts/phase4_resume_generator.py --stage 3 --role {ROLE}")

# ── STAGE 3 ──────────────────────────────────────────────────────────────────
elif STAGE == 3:
    if not check_overwrite(STAGE3_PATH, "Stage 3 review"):
        exit(0)

    jd = load_jd()
    approved = load_text(STAGE2_PATH)

    review = stage3_semantic_review(client, jd, approved)

    with open(STAGE3_PATH, 'w', encoding='utf-8') as f:
        f.write(review)

    print(f"\nStage 3 complete.")
    print(f"  Review saved: {STAGE3_PATH}")
    print(f"\nNext steps:")
    print(f"  1. Open {STAGE3_PATH} in VS Code")
    print(f"  2. Review suggestions — accept or reject each one")
    print(f"  3. Apply accepted changes to {STAGE2_PATH}")
    print(f"  4. Save final version as {STAGE4_PATH}")
    print(f"  5. Run: python scripts/phase4_resume_generator.py --stage 4 --role {ROLE}")

# ── STAGE 4 ──────────────────────────────────────────────────────────────────
elif STAGE == 4:
    # Use stage4_final.txt if exists, otherwise stage2_approved.txt
    input_path = STAGE4_PATH if os.path.exists(STAGE4_PATH) else STAGE2_PATH
    print(f"  Using input: {input_path}")

    if not check_overwrite(
        os.path.join(RESUME_OUTPUT_DIR, f"{ROLE}_Resume.docx"), "Resume .docx"
    ):
        exit(0)

    final_content = load_text(input_path)
    output_path = stage4_generate_docx(final_content, ROLE)

    # Run check_resume.py automatically
    print(f"\n  Running quality check...")
    try:
        check_path = output_path.replace(os.sep, '/')
        result = subprocess.run(
            ["python", CHECK_RESUME_SCRIPT, check_path],
            capture_output=True, text=True, timeout=30
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("  Check stderr:", result.stderr[:200])
        if result.returncode != 0:
            print("  WARNING: Quality check found errors — review before submitting.")
        else:
            print("  Quality check passed.")
    except FileNotFoundError:
        print(f"  WARNING: check_resume.py not found at {CHECK_RESUME_SCRIPT}")
        print("  Run manually: python scripts/check_resume.py " + output_path)
    except Exception as e:
        print(f"  WARNING: Quality check failed to run: {str(e)}")
        print("  Run manually: python scripts/check_resume.py " + output_path)

    print(f"\nStage 4 complete.")
    print(f"  Resume: {output_path}")
    print(f"\nNext steps:")
    print(f"  1. Open {output_path} in Word")
    print(f"  2. Review formatting and adjust if needed")
    print(f"  3. Export to PDF for submission")
    print(f"  4. Update jobs.csv and tracker with application details")
