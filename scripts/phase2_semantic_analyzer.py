# ==============================================
# phase2_semantic_analyzer.py
# Uses Claude API to perform semantic fit analysis
# on each job description against your background
# profile. Produces a nuanced fit score and gap
# analysis that keyword scoring alone cannot match.
# ==============================================

import os
import csv
import json
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# ==============================================
# CONFIGURATION
# ==============================================

JOBS_CSV = "data/jobs.csv"
PACKAGES_DIR = "data/job_packages"
OUTPUT_DIR = "outputs"
RANKED_CSV = os.path.join(OUTPUT_DIR, "ranked_jobs.csv")
SEMANTIC_OUTPUT = os.path.join(OUTPUT_DIR, f"semantic_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt")

# ==============================================
# CANDIDATE BACKGROUND PROFILE
# This is loaded into every API call as context.
# Keep it factual and concise.
# Personal details stay in .env / local files only.
# ==============================================

CANDIDATE_PROFILE = """
CANDIDATE BACKGROUND SUMMARY

Current Level: Senior / Principal Systems Engineer
Clearance: Active TS/SCI
Location: San Diego, CA
Years Experience: 20+

SIGNATURE CREDENTIAL:
Served as the functional MBSE Pillar Lead for Project Overmatch - the CNO's
second-highest priority program. Built and led an eight-person MBSE team from
scratch, translating RADM Small and the Chief Engineer's operational vision into
an implemented MBSE architecture and enterprise-wide integration strategy from
program inception. Navigated significant cross-organizational resistance from
contractor, government, and military stakeholders. Operated with flag-level
visibility in a politically complex environment.

RECENT EXPERIENCE:
- Saronic Technologies (May-Oct 2025): Senior SE for autonomous maritime surface
  vessels. System definition, ICD development, integration planning across
  autonomy, propulsion, communications, and control subsystems.
- KForce/Leidos/NIWC PAC (Aug 2024-Mar 2025): Senior SE for secure tactical
  network capabilities. HAIPE architectures, 35 mission threads, RMF/ATO.
- Shield AI (Nov 2022-Apr 2024): Lead SE for V-BAT / FTUAS program. Cameo/
  MagicDraw MBSE modeling, 3000+ requirements, Class III UAS, two platform
  variants through Phases 1 and 2 of Army FTUAS competition.

TECHNICAL STRENGTHS:
- MBSE: Cameo Systems Modeler (MagicDraw), SysML, Enterprise Architect
- Frameworks: DoDAF expert, UPDM familiar, Navy MBSE frameworks
- Domains: Autonomous systems, C4ISR, maritime/naval, secure comms
- Process: Requirements traceability, verification planning, ICD development,
  ConOps development, system-of-systems architecture

DIFFERENTIATING SKILLS:
- Stakeholder needs analysis: translates operational intent and desired effects
  into performance-based requirements, rather than accepting prescribed solutions
- Startup-to-acquisition bridge: implements repeatable SE processes in fast-paced
  environments that lack formal process maturity
- Organizational leadership: proven track record navigating resistance across
  contractor, government, and military stakeholders

CONSTRAINTS:
- Not a pure hands-on MBSE modeler – best fit is Senior/Lead/Principal level
  roles where architecture, strategy, and stakeholder management are primary
- No aircraft certification (FAA/DO-178) experience
- No formal INCOSE certification
"""

# ==============================================
# SYSTEM PROMPT
# ==============================================

SYSTEM_PROMPT = """You are an expert career coach and systems engineering recruiter
specializing in defense and aerospace talent. You analyze job descriptions against
candidate backgrounds to provide honest, specific fit assessments.

You always:
- Provide specific, actionable analysis grounded in the actual JD text
- Identify genuine strengths AND genuine gaps honestly
- Score on a 1-10 scale where 7+ means strong fit worth pursuing
- Flag roles that are likely poor fits clearly, even if the candidate is interested
- Keep responses structured and concise

You never:
- Inflate scores to make the candidate feel good
- Ignore genuine skill gaps
- Use vague filler language
"""

# ==============================================
# LOAD JOBS
# ==============================================

print("Script started")
print("Loading jobs...")

jobs = []
with open(JOBS_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        jobs.append(row)

# Also load keyword scores if ranked_jobs.csv exists
keyword_scores = {}
if os.path.exists(RANKED_CSV):
    with open(RANKED_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row['company']}_{row['title']}"
            keyword_scores[key] = {
                "score": row.get("score", "N/A"),
                "match_pct": row.get("match_pct", "N/A"),
                "top_keywords": row.get("top_keywords", "N/A")
            }

print(f"Loaded {len(jobs)} jobs")

# ==============================================
# ANALYZE EACH JOB
# ==============================================

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

results = []
report_lines = []

report_lines.append("=" * 60)
report_lines.append("      SEMANTIC FIT ANALYSIS REPORT")
report_lines.append("=" * 60)
report_lines.append(f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")
report_lines.append(f"Jobs analyzed: {len(jobs)}")
report_lines.append("")

for i, job in enumerate(jobs, 1):
    company = job.get("company", "")
    title = job.get("title", "")
    package_folder = job.get("package_folder", "").strip()
    salary = job.get("salary_range", "")

    print(f"Analyzing {i}/{len(jobs)}: {company} | {title}...")

    # Load job description
    description_path = os.path.join(PACKAGES_DIR, package_folder, "job_description.txt")
    if os.path.exists(description_path):
        with open(description_path, encoding='utf-8') as f:
            description = f.read()
    else:
        print(f"  WARNING: No description found for {package_folder}")
        description = "No description available."

    # Get keyword score if available
    key = f"{company}_{title}"
    kw_data = keyword_scores.get(key, {})
    kw_score = kw_data.get("score", "N/A")
    kw_pct = kw_data.get("match_pct", "N/A")
    kw_top = kw_data.get("top_keywords", "N/A")

    # Build the analysis prompt
    prompt = f"""Analyze the fit between this candidate and job description.

CANDIDATE PROFILE:
{CANDIDATE_PROFILE}

JOB DESCRIPTION:
Company: {company}
Title: {title}
Salary: {salary}

{description}

KEYWORD SCORE (from automated keyword matching):
Score: {kw_score} | Match: {kw_pct} | Top keywords: {kw_top}

Please provide your analysis in exactly this format:

FIT SCORE: [1-10]

HEADLINE: [One sentence summary of fit]

TOP 3 STRENGTHS:
1. [Specific strength matched to JD requirements]
2. [Specific strength matched to JD requirements]
3. [Specific strength matched to JD requirements]

TOP 3 GAPS OR RISKS:
1. [Specific gap or risk]
2. [Specific gap or risk]
3. [Specific gap or risk]

RECOMMENDATION: [PURSUE / CONSIDER / SKIP] – [2-3 sentence rationale]

INTERVIEW ANGLE: [If pursuing, what is the strongest narrative to lead with?]
"""

    # Call Claude API
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.content[0].text

    except Exception as e:
        analysis = f"API error: {str(e)}"

    # Store result
    results.append({
        "company": company,
        "title": title,
        "salary": salary,
        "keyword_score": kw_score,
        "keyword_pct": kw_pct,
        "analysis": analysis
    })

    # Add to report
    report_lines.append(f"{'=' * 60}")
    report_lines.append(f"#{i}  {company} | {title}")
    report_lines.append(f"    Salary: {salary} | Keyword Score: {kw_score} ({kw_pct})")
    report_lines.append("")
    report_lines.append(analysis)
    report_lines.append("")

report_lines.append("=" * 60)
report_lines.append(f"Analysis complete: {datetime.now().strftime('%d %b %Y %H:%M')}")
report_lines.append("=" * 60)

# ==============================================
# PRINT AND SAVE REPORT
# ==============================================

report_text = "\n".join(report_lines)
print("\n" + report_text)

os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(SEMANTIC_OUTPUT, "w", encoding="utf-8") as f:
    f.write(report_text)

# ==============================================
# COMBINED RANKING TABLE
# ==============================================

def extract_fit_score(analysis_text):
    for line in analysis_text.split('\n'):
        if line.startswith('FIT SCORE:'):
            try:
                return int(line.split(':')[1].strip().split('/')[0])
            except:
                return 0
    return 0

def extract_recommendation(analysis_text):
    for line in analysis_text.split('\n'):
        if 'RECOMMENDATION:' in line:
            upper = line.upper()
            if 'PURSUE' in upper:
                return 'PURSUE'
            elif 'CONSIDER' in upper:
                return 'CONSIDER'
            elif 'SKIP' in upper:
                return 'SKIP'
    return 'N/A'

# Build combined table
table_data = []
for r in results:
    fit_score = extract_fit_score(r["analysis"])
    recommendation = extract_recommendation(r["analysis"])
    kw_score = r.get("keyword_score", "N/A")
    kw_pct = r.get("keyword_pct", "N/A")
    table_data.append({
        "company":        r["company"],
        "title":          r["title"],
        "salary":         r["salary"],
        "keyword_score":  kw_score,
        "keyword_pct":    kw_pct,
        "fit_score":      fit_score,
        "recommendation": recommendation,
    })

# Sort by fit score descending, then keyword score
table_data.sort(key=lambda x: (x["fit_score"], int(x["keyword_score"]) if str(x["keyword_score"]).isdigit() else 0), reverse=True)

# Truncate title to 28 characters
def trunc(text, length):
    return text if len(text) <= length else text[:length - 2] + ".."

# Format table
table_lines = []
table_lines.append("")
table_lines.append("=" * 95)
table_lines.append("   COMBINED ANALYSIS SUMMARY")
table_lines.append("=" * 95)
table_lines.append(f"{'Rank':<5} {'Company':<22} {'Title':<30} {'Keyword':>8}  {'Sem':>5}  {'Action':<8}  {'Salary'}")
table_lines.append("-" * 95)

for i, r in enumerate(table_data, 1):
    company = trunc(r['company'], 22)
    title = trunc(r['title'], 30)
    kw_pct = r['keyword_pct'] if r['keyword_pct'] != 'N/A' else 'N/A'
    table_lines.append(
        f"{i:<5} {company:<22} {title:<30} "
        f"{str(r['keyword_score']):>4} ({kw_pct:>5})  "
        f"{str(r['fit_score']) + '/10':>5}  "
        f"{r['recommendation']:<8}  "
        f"{r['salary']}"
    )

table_lines.append("=" * 95)
table_lines.append("")

table_text = "\n".join(table_lines)
print(table_text)

# Append table to the saved report
with open(SEMANTIC_OUTPUT, "a", encoding="utf-8") as f:
    f.write(table_text)

print(f"Semantic analysis saved to: {SEMANTIC_OUTPUT}")