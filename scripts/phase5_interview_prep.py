# ==============================================
# phase5_interview_prep.py
# Generates interview preparation materials for
# a specific job application.
#
# Improvements over v1:
#   - Web search via Anthropic API for current
#     company and role information
#   - Resume pull from stage4_final.txt to ground
#     stories in what was actually submitted
#   - Experience library used for employer-attributed
#     STAR story building
#   - PII stripped from all API calls
#
# Outputs to data/job_packages/[role]/interview_prep.txt:
#   Section 1: Company & Role Brief (web-informed)
#   Section 2: Story Bank (library-grounded, employer-attributed)
#   Section 3: Gap Preparation
#   Section 4: Questions to Ask
#
# Usage:
#   python scripts/phase5_interview_prep.py --role Viasat_SE_IS
# ==============================================

import os
import sys
import re
import json
import argparse
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Add project root to path for utils import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils.pii_filter import strip_pii

load_dotenv()

# ==============================================
# CONFIGURATION
# ==============================================

JOBS_PACKAGES_DIR = "data/job_packages"
RESUMES_TAILORED_DIR = "resumes/tailored"
CANDIDATE_PROFILE_PATH = "data/experience_library/candidate_profile.md"
EXPERIENCE_LIBRARY = "data/experience_library/experience_library.json"
OUTPUT_FILENAME = "interview_prep.txt"
OUTPUT_DOCX_FILENAME = "interview_prep.docx"

MODEL = "claude-sonnet-4-20250514"

# ==============================================
# SYSTEM PROMPT
# ==============================================

SYSTEM_PROMPT = """You are an expert career coach specializing in defense and aerospace
systems engineering. You help senior engineers prepare for technical interviews.

You always:
- Ground all stories and claims in the candidate's confirmed experience only
- Use employer attribution in stories ("During my time at G2 OPS..." or
  "When I was supporting Shield AI...")
- Frame stories using STAR format with factually accurate details
- Give honest gap assessments -- never suggest claiming experience not held
- Keep language professional, direct, and confident
- Use en dashes, never em dashes

You never:
- Invent metrics, outcomes, or experience not in the provided background
- Suggest the candidate overstate their role or involvement
- Use vague or generic advice"""

# ==============================================
# STAGE PROFILE CONSTANTS
# ==============================================

_QUESTIONS_RECRUITER = """Generate 4 questions for the candidate to ask during a recruiter screen.

Signal to convey: I've done my homework and I'm a serious candidate.

JOB DESCRIPTION:
{jd}

CANDIDATE BACKGROUND SUMMARY (PII removed):
{profile_summary}

Draw questions from these categories:
- Company direction, growth areas, or recent news
- Culture, team environment, what makes people stay at this company
- Interview process -- who is next, what they evaluate, typical timeline to decision
- Logistics if not already confirmed (clearance requirements, onsite vs. remote, location)

Constraints:
- Maximum 4 questions
- Each question must require insider knowledge to answer -- not answerable from the JD alone
- Do NOT ask about architecture, technical environment, or program pain points
- Do NOT raise salary -- let the recruiter raise it first

Format each question as:
[Number]. [Question] -- [Why ask this / what it signals to the recruiter]

CLOSING NOTE:
[1 sentence: how to close a recruiter screen effectively]"""


_QUESTIONS_HIRING_MANAGER = """Generate 4 questions for the candidate to ask a hiring manager.

Signal to convey: I understand programs and I want to know if this problem is worth solving.

JOB DESCRIPTION:
{jd}

CANDIDATE BACKGROUND SUMMARY (PII removed):
{profile_summary}

Draw questions from these categories:
- Current program pain points -- schedule pressure, architecture debt, stakeholder friction
- What the team currently lacks and needs most
- What success looks like at 6 months vs. what disappointment looks like
- The hiring manager's vision for the technical or engineering effort going forward

Constraints:
- Maximum 4 questions
- Each question must require insider knowledge to answer -- not answerable from the JD alone
- Do NOT ask questions the recruiter should have answered (process, timeline, logistics)
- Questions should signal program-level thinking, not just execution-level

Format each question as:
[Number]. [Question] -- [Why ask this / what it signals to the hiring manager]

CLOSING NOTE:
[1 sentence: how to close a hiring manager interview effectively]"""


_QUESTIONS_TEAM_PANEL = """Generate 4 questions for the candidate to ask a working-level engineering team panel.

Signal to convey: I've been in this seat before and I will be a peer, not a burden.

JOB DESCRIPTION:
{jd}

CANDIDATE BACKGROUND SUMMARY (PII removed):
{profile_summary}

Draw questions from these categories:
- Day-to-day working environment -- tools in active use, cadence, model governance practices
- Where the hard interface or integration problems are right now
- What processes are working well and what is still being figured out
- How the team handles disagreements on architecture or design decisions

Constraints:
- Maximum 4 questions
- Each question must require insider knowledge to answer -- not answerable from the JD alone
- Do NOT ask questions that signal unfamiliarity with standard domain tools
- Do NOT ask management-level or strategy questions -- wrong register for a peer panel
- Tone is collegial and direct -- peer to peer, not candidate to evaluator

Format each question as:
[Number]. [Question] -- [Why ask this / what it signals to the panel]

CLOSING NOTE:
[1 sentence: how to close a team panel effectively]"""


_PEER_FRAME_INSTRUCTIONS = """For each gap identified above, add a fifth element -- Peer Frame.

The Peer Frame is a 2-3 sentence response calibrated for delivery to a working engineer, not a manager.
It differs from the Redirect in register: where a Redirect reassures a manager that risk is manageable,
a Peer Frame signals to a colleague that the candidate understands the operational reality of the gap.

The peer frame should:
1. Acknowledge the specific gap honestly -- no softening or hedging
2. Demonstrate understanding of why the gap matters operationally, not just that it exists
3. Pivot to a question or observation that signals domain fluency

A peer frame that ends with a genuine question is preferred over one that ends with a reassurance.
Length: 2-3 sentences maximum. Tone: direct and collegial.

Add to each gap entry:
Peer Frame: [2-3 sentence response]"""


STAGE_PROFILES = {
    "recruiter": {
        "label": "Recruiter Screen",
        "description": "Short screen \u2013 confirm fit, do not volunteer gaps or technical depth.",
        "story_count": "1-2",
        "story_depth": "headline",
        "gap_behavior": "omit",
        "salary_in_section1": False,
        "section1_focus": "recruiter",
        "questions_prompt": _QUESTIONS_RECRUITER,
    },
    "hiring_manager": {
        "label": "Hiring Manager Interview",
        "description": "60+ min interview \u2013 lead with program context awareness and collaborative framing.",
        "story_count": "3-4",
        "story_depth": "full",
        "gap_behavior": "note",
        "salary_in_section1": True,
        "section1_focus": "hiring_manager",
        "questions_prompt": _QUESTIONS_HIRING_MANAGER,
    },
    "team_panel": {
        "label": "Team Panel Interview",
        "description": "90 min to 3 hr group interview \u2013 lead with technical specificity and process fluency.",
        "story_count": "4-6",
        "story_depth": "full_technical",
        "gap_behavior": "full_peer",
        "salary_in_section1": False,
        "section1_focus": "team_panel",
        "questions_prompt": _QUESTIONS_TEAM_PANEL,
        "peer_frame_prompt": _PEER_FRAME_INSTRUCTIONS,
    },
}

VALID_STAGES = list(STAGE_PROFILES.keys())

# ==============================================
# SALARY EXTRACTION
# ==============================================

def extract_salary(jd_text):
    """Extract salary range from JD and estimate offer guidance."""
    patterns = [
        r'\$\s*([\d,]+(?:\.\d+)?)[kK]?\s*[-\u2013\u2014to]+\s*\$?\s*([\d,]+(?:\.\d+)?)[kK]?',
        r'([\d,]+(?:\.\d+)?)\s*[-\u2013\u2014to]+\s*([\d,]+(?:\.\d+)?)\s*/\s*(?:year|yr|annually)',
    ]
    low = high = None
    for pattern in patterns:
        matches = re.findall(pattern, jd_text, re.IGNORECASE)
        if matches:
            for match in matches:
                try:
                    v1 = float(match[0].replace(',', ''))
                    v2 = float(match[1].replace(',', ''))
                    if v1 < 1000:
                        v1 *= 1000
                    if v2 < 1000:
                        v2 *= 1000
                    if 80000 <= v1 <= 400000 and 80000 <= v2 <= 400000:
                        low, high = min(v1, v2), max(v1, v2)
                        break
                except Exception:
                    continue
            if low and high:
                break

    if not low or not high:
        return {
            'found': False,
            'text': 'Salary range not found in JD',
            'guidance': 'Research Glassdoor, Levels.fyi, and LinkedIn Salary for this role.'
        }

    midpoint = (low + high) / 2
    offer_low = low + (high - low) * 0.45
    offer_high = low + (high - low) * 0.65
    anchor = low + (high - low) * 0.72
    floor = low + (high - low) * 0.35
    anchor_rounded = round(anchor / 5000) * 5000

    return {
        'found': True,
        'text': f"${low:,.0f} \u2013 ${high:,.0f} (midpoint ${midpoint:,.0f})",
        'guidance': (
            f"Posted range: ${low:,.0f} \u2013 ${high:,.0f}\n"
            f"  Realistic offer zone: ${offer_low:,.0f} \u2013 ${offer_high:,.0f} "
            f"(companies rarely open at the top of range)\n"
            f"  Suggested anchor: ${anchor_rounded:,.0f} \u2013 already rounded for natural delivery\n"
            f"  If asked: '${anchor_rounded:,.0f} based on my 20+ years of defense SE "
            f"experience and current TS/SCI clearance, though I am open to "
            f"discussing total compensation.'\n"
            f"  Floor: Do not accept below ${floor:,.0f} for this role level."
        )
    }

# ==============================================
# LOAD RESUME BULLETS FROM STAGE FILE
# ==============================================

def load_resume_bullets(stage4_path, stage2_path):
    """
    Extract bullets and summary from stage4_final.txt (or stage2_approved.txt).
    Stage files are the source of truth -- the .docx is presentation only.
    Returns (resume_data dict, source filename).
    """
    path = source = None
    if os.path.exists(stage4_path):
        path, source = stage4_path, "stage4_final.txt"
    elif os.path.exists(stage2_path):
        path, source = stage2_path, "stage2_approved.txt"
    else:
        return None, None

    with open(path, encoding='utf-8') as f:
        content = f.read()

    resume_data = {'source': source, 'summary': '', 'employers': {}}
    current_section = None
    current_employer = None

    for line in content.split('\n'):
        stripped = line.strip()

        # Skip structural lines
        if (stripped.startswith('=') or stripped.startswith('STAGE') or
                stripped.startswith('Role:') or stripped.startswith('Generated:') or
                stripped.startswith('INSTRUCTIONS') or stripped.startswith('Save as') or
                stripped.startswith('END OF')):
            continue

        if stripped == '## PROFESSIONAL SUMMARY':
            current_section = 'summary'
            continue
        elif stripped == '## CORE COMPETENCIES':
            current_section = 'competencies'
            continue
        elif stripped.startswith('## ') and stripped not in [
                '## PROFESSIONAL SUMMARY', '## CORE COMPETENCIES']:
            current_employer = stripped[3:].strip()
            current_section = 'employer'
            if current_employer not in resume_data['employers']:
                resume_data['employers'][current_employer] = []
            continue

        if current_section == 'summary':
            if stripped and not stripped.startswith('['):
                resume_data['summary'] += (' ' if resume_data['summary'] else '') + stripped

        elif current_section == 'employer' and current_employer:
            if stripped.startswith('- ') and not stripped.startswith('['):
                bullet = stripped[2:].strip()
                bullet = re.sub(r'\s*\[Source:[^\]]*\]', '', bullet).strip()
                bullet = re.sub(r'\s*\[Theme:[^\]]*\]', '', bullet).strip()
                bullet = re.sub(r'\s*\[VERIFY[^\]]*\]', '', bullet).strip()
                if bullet:
                    resume_data['employers'][current_employer].append(bullet)

    return resume_data, source

# ==============================================
# BUILD EMPLOYER-ATTRIBUTED STORY CONTEXT
# ==============================================

def build_story_context(library, resume_data, jd_lower):
    """
    Match resume bullets to library entries to get employer attribution,
    dates, and additional context for STAR story building.
    """
    if not resume_data:
        return "No resume stage file found -- using candidate profile only."

    context_lines = []

    for emp_name, resume_bullets in resume_data['employers'].items():
        if not resume_bullets:
            continue

        # Find matching employer in library
        lib_employer = next(
            (e for e in library['employers']
             if e['name'].upper() == emp_name.upper() or
             emp_name.upper() in e['name'].upper()),
            None
        )

        context_lines.append(f"\n{'='*40}")
        context_lines.append(f"EMPLOYER: {emp_name}")

        if lib_employer:
            context_lines.append(f"Title: {lib_employer.get('title', '')}")
            context_lines.append(f"Dates: {lib_employer.get('dates', '')}")

        context_lines.append("Bullets on submitted resume (use these as story basis):")
        for b in resume_bullets:
            context_lines.append(f"  - {b}")

        # Add relevant library bullets for story depth
        if lib_employer:
            additional = []
            for lb in lib_employer['bullets']:
                if lb.get('flagged'):
                    continue
                kws = lb.get('keywords', [])
                if any(k.lower() in jd_lower for k in kws):
                    if not any(lb['text'][:60] in rb for rb in resume_bullets):
                        additional.append(
                            f"  - [{lb['theme']}] {lb['text'][:150]}"
                        )
            if additional:
                context_lines.append(
                    "Additional library context for story depth (not on resume):"
                )
                context_lines.extend(additional[:4])

    return "\n".join(context_lines)

# ==============================================
# DOCX GENERATION
# ==============================================

def generate_prep_docx(output_path, role, resume_source, stage_profile,
                        section1, section_intro, section2, section3, section4,
                        salary_data):
    """
    Generate a clean formatted .docx interview prep document.
    Uses simple heading/normal/bullet styles -- no resume color scheme.
    """
    doc = Document()

    # Page margins
    from docx.shared import Inches
    sec = doc.sections[0]
    sec.left_margin = Inches(1.0)
    sec.right_margin = Inches(1.0)
    sec.top_margin = Inches(1.0)
    sec.bottom_margin = Inches(1.0)

    def add_heading(text, level=1):
        p = doc.add_heading(text, level=level)
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)

    def add_normal(text):
        p = doc.add_paragraph(text)
        p.paragraph_format.space_after = Pt(4)

    def add_bullet(text):
        p = doc.add_paragraph(text, style='List Bullet')
        p.paragraph_format.space_after = Pt(2)

    def parse_and_add_section(text):
        """
        Parse section text and add to doc with appropriate styles.
        Lines starting with all-caps followed by colon = Heading 3
        Lines starting with bullet markers = List Bullet
        Everything else = Normal
        """
        import re
        for line in text.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue
            # All-caps heading pattern (e.g. "COMPANY OVERVIEW:", "STORY 1 -")
            if (re.match(r'^[A-Z][A-Z\s\-\u2013&/]+[:\-\u2013]', stripped) and
                    len(stripped) < 80 and not stripped.startswith('-')):
                add_heading(stripped, level=2)
            # Bullet lines
            elif stripped.startswith('- ') or stripped.startswith('\u2022 '):
                add_bullet(stripped.lstrip('-\u2022').strip())
            # Numbered items
            elif re.match(r'^\d+\.', stripped):
                add_bullet(stripped)
            # Story labels (Situation:, Task:, Action:, Result:)
            elif re.match(r'^(Situation|Task|Action|Result|Employer|'
                          r'Gap|Honest answer|Bridge|Redirect|'
                          r'If probed|Theme \d|Follow-up):', stripped):
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(2)
                # Label in bold
                label_end = stripped.index(':') + 1
                run1 = p.add_run(stripped[:label_end])
                run1.bold = True
                run2 = p.add_run(stripped[label_end:])
                run2.bold = False
            else:
                add_normal(stripped)

    # Title
    title_p = doc.add_heading('Interview Prep Package', 0)
    title_p.paragraph_format.space_after = Pt(4)

    # Metadata
    add_normal(f"Role: {role}")
    add_normal(f"Stage: {stage_profile['label']}")
    add_normal(f"Stage note: {stage_profile['description']}")
    add_normal(f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")
    if resume_source:
        add_normal(f"Resume source: {resume_source}")
    doc.add_paragraph()

    # Section 1
    add_heading("Company & Role Brief", level=1)
    add_normal("(Web-informed -- verify currency before interview)")
    parse_and_add_section(section1)

    # Section 2
    add_heading("Story Bank", level=1)
    add_normal("Workshop stories before interview -- correct any overreach.")
    parse_and_add_section(section2)

    # Section 3
    add_heading("Gap Preparation", level=1)
    parse_and_add_section(section3)

    # Section 4
    add_heading("Questions to Ask", level=1)
    parse_and_add_section(section4)

    # Salary guidance
    if salary_data['found']:
        add_heading("Salary Guidance", level=1)
        add_normal(salary_data['guidance'])

    doc.save(output_path)

# ==============================================
# CORE GENERATION FUNCTION
# ==============================================

def generate_prep(client, role_data, interview_stage, output_txt_path, output_docx_path,
                  dry_run=False):
    """
    Generate interview prep package from role data.
    role_data keys: jd_text, stage_text, library, candidate_profile, role_name.
    interview_stage: one of VALID_STAGES ('recruiter', 'hiring_manager', 'team_panel').
    dry_run: if True, print stage profile and return without API calls or file writes.
    Writes both .txt and .docx output files.
    All PII stripped from API payloads.
    """
    profile = STAGE_PROFILES[interview_stage]

    jd = role_data["jd_text"]
    raw_stage = role_data.get("stage_text", "")
    library = role_data["library"]
    raw_profile = role_data.get("candidate_profile", "")
    role_name = role_data.get("role_name", "unknown")

    # Strip PII from all text sent to API
    candidate_profile = strip_pii(raw_profile)
    safe_stage = strip_pii(raw_stage)
    jd_lower = jd.lower()

    # Build resume data from stage text (parse inline)
    resume_data = _parse_stage_text(safe_stage, source_label="stage_text")
    resume_source = resume_data.get('source') if resume_data else None

    story_context = build_story_context(library, resume_data, jd_lower)
    salary_data = extract_salary(jd)

    # Extract confirmed gaps section from profile
    gaps_section = ""
    if 'CONFIRMED GAPS' in raw_profile:
        start = raw_profile.find('CONFIRMED GAPS')
        end = raw_profile.find('## STYLE RULES', start)
        gaps_section = strip_pii(raw_profile[start:end if end > 0 else start + 2000])

    # --------------------------------------------------
    # SECTION 1 -- COMPANY & ROLE BRIEF (WEB-INFORMED)
    # --------------------------------------------------
    print("\nSection 1: Company & Role Brief (searching web)...")

    company_prompt = f"""Research this company and role, then generate an interview prep brief.

JOB DESCRIPTION:
{jd[:2500]}

Use the web_search tool to find:
1. Current information about this company's defense/government business
2. The specific business unit mentioned in the JD
3. Recent news, programs, or contracts relevant to this interview

Then provide your brief in this exact format:

COMPANY OVERVIEW:
[3-4 sentences -- what they do, defense/government focus, scale.
Use current web search results where available.]

BUSINESS UNIT OVERVIEW:
[2-3 sentences on the specific business unit for this role.]

ROLE IN CONTEXT:
[2-3 sentences on what this role does day-to-day based on the JD.]

SALARY & LEVEL CONTEXT:
JD posted range: {salary_data['text'] if salary_data['found'] else 'Not found in JD'}
[1-2 sentences on what level this represents and where initial offers typically land.]

SALARY EXPECTATIONS GUIDANCE:
{salary_data['guidance'] if salary_data['found'] else 'Research market rate before interview.'}

KEY TALKING POINTS:
[3 bullet points -- specific, current, factual things showing you researched the company]

RECENT CONTEXT:
[1-2 sentences on current business situation or relevant programs.
Note your source or flag if from training data rather than current search.]"""

    response1 = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": company_prompt}]
    )

    # Extract text blocks from response -- web search returns mixed content types
    section1_parts = []
    for block in response1.content:
        if hasattr(block, 'text') and block.text:
            section1_parts.append(block.text)
    section1 = "\n".join(section1_parts) if section1_parts else \
        "Web search unavailable -- review company website before interview."

    # --------------------------------------------------
    # SECTION 2 -- STORY BANK (LIBRARY-GROUNDED)
    # --------------------------------------------------
    print("Section 2: Story Bank (grounded in resume and library)...")

    story_prompt = f"""Generate employer-attributed STAR interview stories for this role.

CANDIDATE PROFILE (PII removed):
{candidate_profile[:2500]}

RESUME SUBMITTED FOR THIS ROLE -- with employer context:
{story_context[:3000]}

JOB DESCRIPTION:
{jd[:2000]}

CRITICAL INSTRUCTIONS:
- Every story MUST be grounded in the bullets shown above
- Every story MUST include employer attribution
  ("During my time at [Employer as [Title], [dates]...")
- Do NOT invent metrics or outcomes
- Frame results qualitatively when no specific outcome is documented
- Stories should directly address specific JD requirements

Provide in this exact format:

ROLE FIT ASSESSMENT:
[3-4 honest sentences -- strengths and genuine gaps]

KEY THEMES TO LEAD WITH:
Theme 1 -- [Name]: [1-2 sentences on strongest narrative for this role]
Theme 2 -- [Name]: [1-2 sentences]
Theme 3 -- [Name]: [1-2 sentences]

STORY BANK:

STORY 1 -- [JD Requirement this addresses]:
Employer: [Company name | Title | Dates]
Situation: [Context -- what program, environment, challenge]
Task: [What specifically needed to be accomplished]
Action: [What YOU did -- first person, specific to the bullets provided]
Result: [Outcome -- qualitative acceptable, no fabricated numbers]
If probed: [One sentence -- what to add if they ask for more detail]

STORY 2 -- [JD Requirement]:
[same format]

STORY 3 -- [JD Requirement]:
[same format]

STORY 4 -- [JD Requirement]:
[same format]

STORY 5 -- [JD Requirement]:
[same format]

LIKELY INTERVIEW QUESTIONS:
[8 questions likely to be asked, with a one-line approach for each]"""

    response2 = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": story_prompt}]
    )
    section2 = response2.content[0].text

    # --------------------------------------------------
    # SECTION 3 -- GAP PREPARATION
    # --------------------------------------------------
    print("Section 3: Gap Preparation...")

    gap_prompt = f"""You are doing a two-step gap analysis grounded strictly in the JD text and
candidate profile. Follow these steps exactly.

STEP 1 -- EXTRACT ALL JD REQUIREMENTS:
Read the FULL job description below -- including required qualifications, preferred
qualifications, responsibilities, and any other stated criteria. Extract two lists:
  REQUIRED: skills, experience, tools, or credentials explicitly marked as required
  PREFERRED: skills or experience explicitly marked as preferred, desired, or a plus

Do not infer requirements from job type, title, seniority, or industry norms.
Only use what the JD text directly states.

FULL JOB DESCRIPTION:
{jd}

STEP 2 -- CROSS-REFERENCE AGAINST CANDIDATE PROFILE:
Compare your extracted lists against the candidate profile below. A gap is valid if:
  - HARD GAP: JD lists it as REQUIRED and it is either in the confirmed gaps section
    OR clearly absent from the candidate's documented experience
  - PREFERRED GAP: JD lists it as PREFERRED and it is absent from the profile --
    flag these as "preferred but not held" (lower severity)

Do NOT flag anything based on inference, assumption, or industry norms.
Only flag what the JD text explicitly states as required or preferred.

Expect to find 3-5 gaps for a typical senior engineering role. If you find zero,
re-examine the preferred qualifications section -- gaps there count.

CANDIDATE CONFIRMED GAPS:
{gaps_section[:1500]}

CANDIDATE FULL PROFILE (for cross-referencing skills not in confirmed gaps):
{candidate_profile[:2000]}

For each gap provide a direct, confident talking point -- not apologetic.

Format exactly as:

GAP 1 -- [Topic] [REQUIRED or PREFERRED]:
Gap: [What the JD states (quote or close paraphrase) and why it's a gap]
Honest answer: [What to say -- confident, not apologetic]
Bridge: [Connection to actual experience]
Redirect: [Strength to pivot toward]

GAP 2 -- [Topic] [REQUIRED or PREFERRED]:
[same format]

GAP 3 -- [Topic] [REQUIRED or PREFERRED]:
[same format]

HARD QUESTIONS TO PREPARE FOR:
[5 questions that will probe these gaps, with one-sentence approach each]"""

    response3 = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": gap_prompt}]
    )
    section3 = response3.content[0].text

    # --------------------------------------------------
    # SECTION 4 -- QUESTIONS TO ASK
    # --------------------------------------------------
    print("Section 4: Questions to Ask...")

    questions_prompt = f"""Generate thoughtful questions for the candidate to ask
during a 45-minute phone interview for this role.

JOB DESCRIPTION:
{jd[:2000]}

CANDIDATE BACKGROUND SUMMARY (PII removed):
{strip_pii(candidate_profile[:800])}

Generate 8 questions in three categories. Each should demonstrate genuine
domain knowledge -- not generic interview questions.

QUESTIONS ABOUT THE ROLE & TEAM:
1. [Question] -- [Why ask this / what expertise it signals]
2. [Question] -- [Why ask this / what expertise it signals]
3. [Question] -- [Why ask this / what expertise it signals]

QUESTIONS ABOUT THE PROGRAM & TECHNICAL ENVIRONMENT:
4. [Question] -- [Why ask this / what expertise it signals]
5. [Question] -- [Why ask this / what expertise it signals]
6. [Question] -- [Why ask this / what expertise it signals]

QUESTIONS ABOUT SUCCESS & GROWTH:
7. [Question] -- [Why ask this / what expertise it signals]
8. [Question] -- [Why ask this / what expertise it signals]

CLOSING NOTE:
[1-2 sentences on how to close the interview effectively]"""

    response4 = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": questions_prompt}]
    )
    section4 = response4.content[0].text

    # --------------------------------------------------
    # COMPILE AND SAVE OUTPUT
    # --------------------------------------------------
    print("\nCompiling output...")

    output_lines = []
    output_lines.append("=" * 60)
    output_lines.append("INTERVIEW PREP PACKAGE v2")
    output_lines.append("=" * 60)
    output_lines.append(f"Role: {role_name}")
    output_lines.append(f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")
    output_lines.append(f"Resume source: {resume_source if resume_source else 'Not found'}")
    output_lines.append("Note: PII stripped from all API calls.")
    output_lines.append("=" * 60)
    output_lines.append("")

    output_lines.append("SECTION 1 \u2013 COMPANY & ROLE BRIEF")
    output_lines.append("(Web-informed -- verify currency before interview)")
    output_lines.append("-" * 60)
    output_lines.append(section1)
    output_lines.append("")

    output_lines.append("=" * 60)
    output_lines.append("SECTION 2 \u2013 STORY BANK")
    output_lines.append("(Grounded in submitted resume with employer attribution)")
    output_lines.append("REMINDER: Workshop stories in chat before interview.")
    output_lines.append("Correct any overreach -- every detail must be accurate.")
    output_lines.append("-" * 60)
    output_lines.append(section2)
    output_lines.append("")

    output_lines.append("=" * 60)
    output_lines.append("SECTION 3 \u2013 GAP PREPARATION")
    output_lines.append("-" * 60)
    output_lines.append(section3)
    output_lines.append("")

    output_lines.append("=" * 60)
    output_lines.append("SECTION 4 \u2013 QUESTIONS TO ASK")
    output_lines.append("-" * 60)
    output_lines.append(section4)
    output_lines.append("")

    output_lines.append("=" * 60)
    output_lines.append("END OF INTERVIEW PREP PACKAGE")
    output_lines.append(f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")
    output_lines.append("=" * 60)

    output_text = "\n".join(output_lines)

    with open(output_txt_path, 'w', encoding='utf-8') as f:
        f.write(output_text)
    print(f"  Interview prep written to {output_txt_path}")

    # Generate docx
    try:
        generate_prep_docx(
            output_docx_path, role_name, resume_source, profile,
            section1, "", section2, section3, section4,
            salary_data
        )
        print(f"  Interview prep .docx written to {output_docx_path}")
    except Exception as e:
        print(f"  WARNING: Docx generation failed: {str(e)}")
        print(f"  Text file is still available: {output_txt_path}")
        # Still create a minimal docx so the file exists
        doc = Document()
        for line in output_text.splitlines():
            doc.add_paragraph(line)
        doc.save(output_docx_path)


def _parse_stage_text(stage_text, source_label="stage_text"):
    """
    Parse a stage file text string into resume_data dict.
    Mirrors load_resume_bullets() but operates on a string instead of a file path.
    """
    if not stage_text or not stage_text.strip():
        return None

    resume_data = {'source': source_label, 'summary': '', 'employers': {}}
    current_section = None
    current_employer = None

    for line in stage_text.split('\n'):
        stripped = line.strip()

        # Skip structural lines
        if (stripped.startswith('=') or stripped.startswith('STAGE') or
                stripped.startswith('Role:') or stripped.startswith('Generated:') or
                stripped.startswith('INSTRUCTIONS') or stripped.startswith('Save as') or
                stripped.startswith('END OF')):
            continue

        if stripped == '## PROFESSIONAL SUMMARY':
            current_section = 'summary'
            continue
        elif stripped == '## CORE COMPETENCIES':
            current_section = 'competencies'
            continue
        elif stripped.startswith('## ') and stripped not in [
                '## PROFESSIONAL SUMMARY', '## CORE COMPETENCIES']:
            current_employer = stripped[3:].strip()
            current_section = 'employer'
            if current_employer not in resume_data['employers']:
                resume_data['employers'][current_employer] = []
            continue

        if current_section == 'summary':
            if stripped and not stripped.startswith('['):
                resume_data['summary'] += (' ' if resume_data['summary'] else '') + stripped

        elif current_section == 'employer' and current_employer:
            if stripped.startswith('- ') and not stripped.startswith('['):
                bullet = stripped[2:].strip()
                bullet = re.sub(r'\s*\[Source:[^\]]*\]', '', bullet).strip()
                bullet = re.sub(r'\s*\[Theme:[^\]]*\]', '', bullet).strip()
                bullet = re.sub(r'\s*\[VERIFY[^\]]*\]', '', bullet).strip()
                if bullet:
                    resume_data['employers'][current_employer].append(bullet)

    return resume_data

# ==============================================
# MAIN
# ==============================================

def main():
    parser = argparse.ArgumentParser(description='Phase 5 Interview Prep Generator')
    parser.add_argument('--role', type=str, required=True,
                        help='Role package folder name (e.g. Viasat_SE_IS)')
    parser.add_argument('--interview_stage', type=str, default=None,
                        choices=VALID_STAGES,
                        help=f'Interview stage: {", ".join(VALID_STAGES)}')
    parser.add_argument('--dry_run', action='store_true',
                        help='Print stage profile and exit without generating output')
    args = parser.parse_args()

    role = args.role
    interview_stage = args.interview_stage

    # Interactive fallback if stage not provided
    if not interview_stage:
        print("\nSelect interview stage:")
        for i, s in enumerate(VALID_STAGES, 1):
            p = STAGE_PROFILES[s]
            print(f"  {i}. {s} – {p['label']}: {p['description']}")
        choice = input("Enter stage name or number (1-3): ").strip().lower()
        if choice in ("1", "recruiter"):
            interview_stage = "recruiter"
        elif choice in ("2", "hiring_manager"):
            interview_stage = "hiring_manager"
        elif choice in ("3", "team_panel"):
            interview_stage = "team_panel"
        else:
            print(f"Invalid selection '{choice}'. Valid stages: {', '.join(VALID_STAGES)}")
            sys.exit(1)

    package_dir = os.path.join(JOBS_PACKAGES_DIR, role)
    jd_path = os.path.join(package_dir, "job_description.txt")
    stage4_path = os.path.join(package_dir, "stage4_final.txt")
    stage2_path = os.path.join(package_dir, "stage2_approved.txt")
    output_txt_path = os.path.join(package_dir, f"interview_prep_{interview_stage}.txt")
    output_docx_path = os.path.join(package_dir, f"interview_prep_{interview_stage}.docx")

    print("=" * 60)
    print("PHASE 5 \u2013 INTERVIEW PREP GENERATOR v2")
    print("=" * 60)
    print(f"Role: {role}")
    print(f"Package: {package_dir}")

    errors = []
    if not os.path.exists(package_dir):
        errors.append(f"Job package folder not found: {package_dir}")
    if not os.path.exists(jd_path):
        errors.append(f"job_description.txt not found in {package_dir}")
    if not os.path.exists(CANDIDATE_PROFILE_PATH):
        errors.append(f"candidate_profile.md not found: {CANDIDATE_PROFILE_PATH}")
    if not os.path.exists(EXPERIENCE_LIBRARY):
        errors.append(f"experience_library.json not found: {EXPERIENCE_LIBRARY}")

    if errors:
        print("\nERRORS -- cannot proceed:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)

    print("\nLoading data...")

    with open(jd_path, encoding='utf-8') as f:
        jd_text = f.read()

    with open(CANDIDATE_PROFILE_PATH, encoding='utf-8') as f:
        candidate_profile = f.read()

    with open(EXPERIENCE_LIBRARY, encoding='utf-8') as f:
        library = json.load(f)
    print(f"  Experience library loaded: {library['metadata']['total_bullets']} bullets")

    # Load stage file text
    stage_text = ""
    if os.path.exists(stage4_path):
        with open(stage4_path, encoding='utf-8') as f:
            stage_text = f.read()
        print(f"  Resume loaded from stage4_final.txt")
    elif os.path.exists(stage2_path):
        with open(stage2_path, encoding='utf-8') as f:
            stage_text = f.read()
        print(f"  Resume loaded from stage2_approved.txt")
    else:
        print(f"  WARNING: No stage file found -- stories will use library only")

    # Overwrite protection
    if os.path.exists(output_txt_path):
        print(f"\nWARNING: interview_prep_{interview_stage}.txt already exists.")
        overwrite = input("  Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("  Cancelled. Existing file preserved.")
            sys.exit(0)

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    role_data = {
        "jd_text": jd_text,
        "stage_text": stage_text,
        "library": library,
        "candidate_profile": candidate_profile,
        "role_name": role,
    }

    generate_prep(client, role_data, interview_stage, output_txt_path, output_docx_path,
                  dry_run=args.dry_run)

    print(f"\n{'=' * 60}")
    print("PHASE 5 COMPLETE")
    print(f"{'=' * 60}")
    print(f"Output saved: {output_txt_path}")
    print(f"\nNext steps:")
    print(f"  1. Open {output_docx_path} in Word for formatted reading")
    print(f"     Or open {output_txt_path} in VS Code (View > Word Wrap)")
    print(f"  2. Verify company brief accuracy (web results may be stale)")
    print(f"  3. Workshop STAR stories in chat -- correct any overreach")
    print(f"  4. Practice gap answers out loud -- confident, not apologetic")
    print(f"  5. Select 4-5 questions from Section 4")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
