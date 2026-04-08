# ==============================================
# phase2_semantic_analyzer.py
# Uses Claude API to perform semantic fit analysis
# on job descriptions against candidate background.
#
# Only analyzes PURSUE and CONSIDER roles from
# jobs.csv - skips SKIP, APPLIED, and blank/NEW.
# Run phase2_job_ranking.py first and assign
# PURSUE/CONSIDER status before running this.
# ==============================================

import os
import csv
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
from scripts.utils.pii_filter import strip_pii

load_dotenv()

# ==============================================
# CONFIGURATION
# ==============================================

JOBS_CSV = "data/jobs.csv"
PACKAGES_DIR = "data/job_packages"
OUTPUT_DIR = "outputs"
RANKED_CSV = os.path.join(OUTPUT_DIR, "ranked_jobs.csv")
CANDIDATE_PROFILE_PATH = "data/experience_library/candidate_profile.md"

MODEL = "claude-sonnet-4-20250514"

# Only these statuses get semantic analysis - API calls cost money
ANALYZE_STATUSES = {"PURSUE", "CONSIDER"}

# ==============================================
# LOAD CANDIDATE PROFILE
# ==============================================

def load_candidate_profile():
    if os.path.exists(CANDIDATE_PROFILE_PATH):
        with open(CANDIDATE_PROFILE_PATH, encoding='utf-8') as f:
            return f.read()
    else:
        print(f"WARNING: candidate_profile.md not found at {CANDIDATE_PROFILE_PATH}")
        print("  Run phase3_build_candidate_profile.py to generate it.")
        print("  Using fallback minimal profile.")
        return """
CANDIDATE: [CANDIDATE]
CLEARANCE: Current TS/SCI
LOCATION: San Diego, CA
EXPERIENCE: 20+ years defense systems engineering
SIGNATURE CREDENTIAL: Functional MBSE Pillar Lead, Project Overmatch (CNO priority)
CONSTRAINTS: Not a pure modeler, no FAA/DO-178, no INCOSE certification
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
# ANALYZE A SINGLE JOB
# ==============================================

def analyze_job(client, job, jd_text, candidate_profile, keyword_scores):
    """
    Run semantic analysis for a single job using the Claude API.
    candidate_profile PII is stripped before sending.
    Returns the API response text, or an error string on failure.
    """
    company = job.get("company", "Unknown")
    title = job.get("title", "Unknown")
    key = f"{company}_{title}"
    kw_info = keyword_scores.get(key, {})

    safe_profile = strip_pii(candidate_profile)
    safe_jd = strip_pii(jd_text)

    prompt = f"""Analyze this job description against the candidate background.

CANDIDATE BACKGROUND:
{safe_profile}

JOB: {company} | {title}
KEYWORD SCORE: {kw_info.get('score', 'N/A')} ({kw_info.get('match_pct', 'N/A')}% match)
TOP KEYWORDS: {kw_info.get('top_keywords', 'N/A')}

JOB DESCRIPTION:
{safe_jd}

Provide: fit score (1-10), key strengths, genuine gaps, recommendation (PURSUE/CONSIDER/SKIP).
"""
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        return f"[API ERROR: {e}]"

# ==============================================
# HELPER FUNCTIONS
# ==============================================

def extract_fit_score(analysis_text):
    for line in analysis_text.split('\n'):
        if line.startswith('FIT SCORE:'):
            try:
                return int(line.split(':')[1].strip().split('/')[0])
            except Exception:
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


def trunc(text, length):
    return text if len(text) <= length else text[:length - 2] + ".."


# ==============================================
# MAIN
# ==============================================

def main():
    SEMANTIC_OUTPUT = os.path.join(
        OUTPUT_DIR,
        f"semantic_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    )

    candidate_profile = load_candidate_profile()

    print("Script started")
    print("Loading jobs...")

    all_jobs = []
    with open(JOBS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_jobs.append(row)

    # Filter to only PURSUE and CONSIDER
    jobs_to_analyze = [
        j for j in all_jobs
        if j.get("status", "").strip().upper() in ANALYZE_STATUSES
    ]

    skipped = len(all_jobs) - len(jobs_to_analyze)

    print(f"Total jobs in pipeline: {len(all_jobs)}")
    print(f"Analyzing: {len(jobs_to_analyze)} (PURSUE + CONSIDER)")
    print(f"Skipping: {skipped} (NEW, SKIP, APPLIED)")

    if not jobs_to_analyze:
        print("\nNo PURSUE or CONSIDER roles found.")
        print("Run phase2_job_ranking.py first and assign PURSUE or CONSIDER status.")
        return

    # Load keyword scores from ranked_jobs.csv if available
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

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    results = []
    report_lines = []

    report_lines.append("=" * 60)
    report_lines.append("      SEMANTIC FIT ANALYSIS REPORT")
    report_lines.append("=" * 60)
    report_lines.append(f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")
    report_lines.append(f"Roles analyzed: {len(jobs_to_analyze)} (PURSUE + CONSIDER only)")
    report_lines.append(f"Roles skipped: {skipped} (NEW, SKIP, APPLIED)")
    report_lines.append("")

    for i, job in enumerate(jobs_to_analyze, 1):
        company = job.get("company", "")
        title = job.get("title", "")
        package_folder = job.get("package_folder", "").strip()
        salary = job.get("salary_range", "")
        status = job.get("status", "").strip().upper()

        print(f"Analyzing {i}/{len(jobs_to_analyze)}: {company} | {title} [{status}]...")

        # Load job description
        description_path = os.path.join(PACKAGES_DIR, package_folder, "job_description.txt")
        if os.path.exists(description_path):
            with open(description_path, encoding='utf-8') as f:
                description = f.read()
        else:
            print(f"  WARNING: No description found for {package_folder}")
            description = "No description available."

        # Get keyword score info for this job
        key = f"{company}_{title}"
        kw_data = keyword_scores.get(key, {})
        kw_score = kw_data.get("score", "N/A")
        kw_pct = kw_data.get("match_pct", "N/A")

        analysis = analyze_job(client, job, description, candidate_profile, keyword_scores)

        results.append({
            "company":       company,
            "title":         title,
            "salary":        salary,
            "status":        status,
            "keyword_score": kw_score,
            "keyword_pct":   kw_pct,
            "analysis":      analysis
        })

        report_lines.append("=" * 60)
        report_lines.append(f"#{i}  [{status}]  {company} | {title}")
        report_lines.append(f"    Salary: {salary} | Keyword Score: {kw_score} ({kw_pct})")
        report_lines.append("")
        report_lines.append(analysis)
        report_lines.append("")

    report_lines.append("=" * 60)
    report_lines.append(f"Analysis complete: {datetime.now().strftime('%d %b %Y %H:%M')}")
    report_lines.append("=" * 60)

    # ==============================================
    # SAVE REPORT
    # ==============================================

    report_text = "\n".join(report_lines)
    print("\n" + report_text)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(SEMANTIC_OUTPUT, "w", encoding="utf-8") as f:
        f.write(report_text)

    # ==============================================
    # COMBINED RANKING TABLE
    # ==============================================

    # Build combined table
    table_data = []
    for r in results:
        fit_score = extract_fit_score(r["analysis"])
        recommendation = extract_recommendation(r["analysis"])
        table_data.append({
            "company":        r["company"],
            "title":          r["title"],
            "salary":         r["salary"],
            "status":         r["status"],
            "keyword_score":  r.get("keyword_score", "N/A"),
            "keyword_pct":    r.get("keyword_pct", "N/A"),
            "fit_score":      fit_score,
            "recommendation": recommendation,
        })

    # Sort by fit score descending, then keyword score
    table_data.sort(
        key=lambda x: (x["fit_score"],
                       int(x["keyword_score"]) if str(x["keyword_score"]).isdigit() else 0),
        reverse=True
    )

    table_lines = []
    table_lines.append("")
    table_lines.append("=" * 100)
    table_lines.append("   COMBINED ANALYSIS SUMMARY")
    table_lines.append("=" * 100)
    table_lines.append(f"{'Rank':<5} {'St':<8} {'Company':<22} {'Title':<28} {'Keyword':>8}  {'Sem':>5}  {'Action':<8}  {'Salary'}")
    table_lines.append("-" * 100)

    for i, r in enumerate(table_data, 1):
        company = trunc(r['company'], 22)
        title = trunc(r['title'], 28)
        kw_pct = r['keyword_pct'] if r['keyword_pct'] != 'N/A' else 'N/A'
        table_lines.append(
            f"{i:<5} {r['status']:<8} {company:<22} {title:<28} "
            f"{str(r['keyword_score']):>4} ({kw_pct:>5})  "
            f"{str(r['fit_score']) + '/10':>5}  "
            f"{r['recommendation']:<8}  "
            f"{r['salary']}"
        )

    table_lines.append("=" * 100)
    table_lines.append("")
    table_lines.append("Next steps:")
    table_lines.append("  1. Review full analysis above for each role")
    table_lines.append("  2. Update status in jobs.csv based on findings")
    table_lines.append("  3. Run phase4_resume_generator.py for top PURSUE roles")
    table_lines.append("  4. Update tracker once applications are submitted")
    table_lines.append("=" * 100)

    table_text = "\n".join(table_lines)
    print(table_text)

    with open(SEMANTIC_OUTPUT, "a", encoding="utf-8") as f:
        f.write(table_text)

    print(f"\nSemantic analysis saved to: {SEMANTIC_OUTPUT}")


if __name__ == "__main__":
    main()
