# ==============================================
# phase2_job_ranking.py
# Reads jobs.csv and job description text files,
# scores each role against a weighted keyword
# profile, and produces a ranked shortlist.
#
# Status workflow:
#   blank   = new, not yet reviewed - appears in report
#   PURSUE  = apply next - appears in report
#   CONSIDER = on deck - appears in report
#   SKIP    = decided against - excluded from report
#   APPLIED = submitted - excluded from report
# ==============================================

import csv
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ==============================================
# CONFIGURATION
# ==============================================

JOBS_CSV = "data/jobs.csv"
PACKAGES_DIR = "data/job_packages"
OUTPUT_DIR = "outputs"
RANKED_OUTPUT = os.path.join(OUTPUT_DIR, "ranked_jobs.csv")
REPORT_OUTPUT = os.path.join(OUTPUT_DIR, f"ranking_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt")

# Status values that appear in the ranked report
ACTIONABLE_STATUSES = {"", "PURSUE", "CONSIDER"}

# Status values excluded from the ranked report
EXCLUDED_STATUSES = {"SKIP", "APPLIED"}

# ==============================================
# KEYWORD SCORING PROFILE
# Format: ("keyword", weight, ["aliases"])
# ==============================================

KEYWORDS = [
    # Technical - MBSE & Architecture
    ("MBSE",                    7,  ["model based systems engineering", "model-based systems engineering"]),
    ("Cameo",                   6,  ["MagicDraw", "cameo systems modeler"]),
    ("DoDAF",                   6,  ["department of defense architecture framework"]),
    ("System-of-Systems",       7,  ["system of systems", "SoS"]),
    ("Architecture",            6,  ["architect"]),

    # Domain
    ("Autonomous Systems",      8,  ["autonomy", "autonomous"]),
    ("Uncrewed",                7,  ["UAS", "UAV", "unmanned", "uncrewed aerial", "uncrewed surface"]),
    ("Maritime",                7,  ["naval", "Navy", "USN", "surface vessel"]),
    ("C4ISR",                   7,  ["C2", "command and control", "ISR"]),
    ("NAVWAR",                  6,  ["SPAWAR", "NIWC"]),
    ("Defense",                 5,  ["DoD", "Department of Defense", "military"]),

    # Role Level & Leadership
    ("Lead",                    7,  ["principal", "staff engineer", "senior staff"]),
    ("Team Lead",               6,  ["team leadership", "led a team", "leading a team"]),
    ("IPT",                     5,  ["integrated product team"]),

    # Acquisition & Process
    ("Defense Acquisition",     6,  ["acquisition program", "ACAT", "DAU", "JCIDS"]),
    ("Requirements Traceability", 6, ["requirements management", "traceability matrix"]),
    ("Verification",            5,  ["validation", "V&V", "test and evaluation"]),
    ("Integration",             5,  ["systems integration", "integration planning"]),
    ("Performance-Based Requirements", 5, ["performance requirements", "shall statements"]),
    ("ICD",                     6,  ["interface control document", "interface definition"]),
    ("ConOps",                  6,  ["concept of operations", "CONOPS"]),

    # Stakeholder & Mission
    ("Stakeholder Engagement",  7,  ["stakeholder management", "customer engagement"]),
    ("Operational Needs",       7,  ["operational requirements", "needs analysis", "operational need"]),
    ("Mission Analysis",        7,  ["mission thread", "mission engineering", "mission systems"]),
    ("Operational Effects",     6,  ["effects-based", "desired effects", "mission effects"]),

    # High-Value Flags
    ("Project Overmatch",       10, ["overmatch", "DRPM Overmatch"]),
    ("JADC2",                   8,  ["joint all domain command and control", "all domain"]),
    ("Mission Thread",          7,  ["mission threads"]),
]

# ==============================================
# SCORING FUNCTION
# ==============================================

def score_job(description):
    """
    Score a job description against the keyword profile.
    Returns total score and a dict of matched keywords.
    """
    description_lower = description.lower()
    matched = {}
    total_score = 0

    for keyword, weight, aliases in KEYWORDS:
        all_terms = [keyword.lower()] + [a.lower() for a in aliases]
        for term in all_terms:
            if term in description_lower:
                matched[keyword] = weight
                total_score += weight
                break

    return total_score, matched


# ==============================================
# DUPLICATE DETECTION
# ==============================================

def detect_duplicates(results):
    """
    Find duplicate req numbers in a list of scored job results.
    Returns list of tuples: (req_number, first_label, dupe_company, dupe_title)
    """
    req_seen = {}
    duplicates = []
    for r in results:
        req = r.get("req_number", "").strip()
        if req:
            if req in req_seen:
                duplicates.append((req, req_seen[req], r["company"], r["title"]))
            else:
                req_seen[req] = f"{r['company']} | {r['title']}"
    return duplicates


# ==============================================
# MAIN
# ==============================================

def main():

    # ==============================================
    # LOAD JOBS
    # ==============================================

    print("Script started")
    print("Loading jobs from CSV...")

    jobs = []
    with open(JOBS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jobs.append(row)

    print(f"Loaded {len(jobs)} jobs")

    # ==============================================
    # SCORE ALL JOBS
    # ==============================================

    print("Scoring jobs...")

    all_results = []

    for job in jobs:
        package_folder = job.get("package_folder", "").strip()
        status = job.get("status", "").strip().upper()
        description_path = os.path.join(PACKAGES_DIR, package_folder, "job_description.txt")

        # Load job description
        if os.path.exists(description_path):
            with open(description_path, encoding='utf-8') as f:
                description = f.read()
        else:
            if status not in EXCLUDED_STATUSES:
                print(f"  WARNING: No description found for {package_folder}")
            description = ""

        # Score the job
        score, matched_keywords = score_job(description)
        max_possible = sum(w for _, w, _ in KEYWORDS)
        match_pct = round((score / max_possible) * 100, 1)

        all_results.append({
            "company":          job.get("company", ""),
            "title":            job.get("title", ""),
            "location":         job.get("location", ""),
            "salary_range":     job.get("salary_range", ""),
            "url":              job.get("url", ""),
            "req_number":       job.get("req_number", "").strip(),
            "date_found":       job.get("date_found", ""),
            "status":           status,
            "package_folder":   package_folder,
            "score":            score,
            "match_pct":        match_pct,
            "matched_keywords": matched_keywords,
        })

    # Sort all results by score descending
    all_results.sort(key=lambda x: x["score"], reverse=True)

    # Split into actionable and excluded
    actionable = [r for r in all_results if r["status"] in ACTIONABLE_STATUSES]
    excluded = [r for r in all_results if r["status"] in EXCLUDED_STATUSES]

    print(f"Scoring complete")
    print(f"  Actionable (blank/PURSUE/CONSIDER): {len(actionable)}")
    print(f"  Excluded (SKIP/APPLIED): {len(excluded)}")

    # ==============================================
    # SAVE RANKED CSV - actionable roles only
    # ==============================================

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(RANKED_OUTPUT, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "status", "company", "title", "location",
                         "salary_range", "req_number", "score", "match_pct",
                         "top_keywords", "url", "package_folder"])
        for i, r in enumerate(actionable, 1):
            top_keywords = ", ".join(
                f"{k}({v})" for k, v in
                sorted(r["matched_keywords"].items(), key=lambda x: -x[1])[:5]
            )
            writer.writerow([
                i,
                r["status"] if r["status"] else "NEW",
                r["company"],
                r["title"],
                r["location"],
                r["salary_range"],
                r["req_number"],
                r["score"],
                f"{r['match_pct']}%",
                top_keywords,
                r["url"],
                r["package_folder"],
            ])

    print(f"Ranked CSV saved to: {RANKED_OUTPUT}")

    # ==============================================
    # PRINT REPORT
    # ==============================================

    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("         JOB RANKING REPORT")
    report_lines.append("=" * 60)
    report_lines.append(f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")
    report_lines.append(f"Total jobs in pipeline: {len(all_results)}")
    report_lines.append(f"Max possible score: {sum(w for _, w, _ in KEYWORDS)}")
    report_lines.append("")

    # Status summary
    status_counts = {}
    for r in all_results:
        s = r["status"] if r["status"] else "NEW"
        status_counts[s] = status_counts.get(s, 0) + 1

    report_lines.append("PIPELINE STATUS SUMMARY")
    report_lines.append("-" * 40)
    for status in ["NEW", "PURSUE", "CONSIDER", "APPLIED", "SKIP"]:
        count = status_counts.get(status, 0)
        if count > 0:
            report_lines.append(f"  {status:<10} {count}")
    report_lines.append("")

    # Duplicate req number detection
    duplicates = detect_duplicates(all_results)

    if duplicates:
        report_lines.append("DUPLICATE REQ NUMBERS DETECTED")
        report_lines.append("-" * 40)
        for req, first, company, title in duplicates:
            report_lines.append(f"  REQ {req}:")
            report_lines.append(f"    First:  {first}")
            report_lines.append(f"    Second: {company} | {title}")
        report_lines.append("")

    # Actionable roles - ranked
    report_lines.append(f"ACTIONABLE ROLES ({len(actionable)} roles - NEW, PURSUE, CONSIDER)")
    report_lines.append("=" * 60)
    report_lines.append("")

    if not actionable:
        report_lines.append("  No actionable roles - all roles have been reviewed.")
        report_lines.append("  Add new roles to jobs.csv to continue.")
    else:
        for i, r in enumerate(actionable, 1):
            status_label = r["status"] if r["status"] else "NEW"
            req_display = f"  |  Req: {r['req_number']}" if r.get('req_number') else ""
            report_lines.append(f"#{i}  [{status_label}]  {r['company']} | {r['title']}{req_display}")
            report_lines.append(f"    Location: {r['location']}  |  Salary: {r['salary_range']}")
            report_lines.append(f"    Score: {r['score']} ({r['match_pct']}% match)")
            report_lines.append(f"    Matched keywords:")
            for kw, wt in sorted(r["matched_keywords"].items(), key=lambda x: -x[1]):
                report_lines.append(f"      + {kw} ({wt})")
            report_lines.append("")

    report_lines.append("=" * 60)
    report_lines.append("Next steps:")
    report_lines.append("  1. Update status in jobs.csv:")
    report_lines.append("     PURSUE  = apply next")
    report_lines.append("     CONSIDER = needs more thought")
    report_lines.append("     SKIP    = decided against")
    report_lines.append("  2. Run phase2_semantic_analyzer.py for PURSUE and CONSIDER roles")
    report_lines.append("  3. Apply to top roles, update status to APPLIED")
    report_lines.append("  4. Move APPLIED entries to job_pipeline.xlsx tracker")
    report_lines.append("=" * 60)

    report_text = "\n".join(report_lines)
    print("\n" + report_text)

    # Save report
    with open(REPORT_OUTPUT, "w", encoding='utf-8') as f:
        f.write(report_text)

    print(f"\nReport saved to: {REPORT_OUTPUT}")


if __name__ == "__main__":
    main()
