# ==============================================
# phase2_job_ranking.py
# Reads jobs.csv and job description text files,
# scores each role against a weighted keyword
# profile, and produces a ranked shortlist.
# ==============================================

import csv
import os
import json
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

# ==============================================
# KEYWORD SCORING PROFILE
# Format: ("keyword", weight, ["aliases"])
# Aliases are alternative forms of the same keyword
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
        # Check primary keyword
        all_terms = [keyword.lower()] + [a.lower() for a in aliases]
        for term in all_terms:
            if term in description_lower:
                matched[keyword] = weight
                total_score += weight
                break  # Only count each keyword once

    return total_score, matched

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
# SCORE EACH JOB
# ==============================================

print("Scoring jobs...")

results = []

for job in jobs:
    package_folder = job.get("package_folder", "").strip()
    description_path = os.path.join(PACKAGES_DIR, package_folder, "job_description.txt")

    # Load job description text
    if os.path.exists(description_path):
        with open(description_path, encoding='utf-8') as f:
            description = f.read()
    else:
        print(f"  WARNING: No description found for {package_folder} at {description_path}")
        description = ""

    # Score the job
    score, matched_keywords = score_job(description)

    # Calculate match percentage against maximum possible score
    max_possible = sum(w for _, w, _ in KEYWORDS)
    match_pct = round((score / max_possible) * 100, 1)

    results.append({
        "company":          job.get("company", ""),
        "title":            job.get("title", ""),
        "location":         job.get("location", ""),
        "salary_range":     job.get("salary_range", ""),
        "url":              job.get("url", ""),
        "date_found":       job.get("date_found", ""),
        "package_folder":   package_folder,
        "score":            score,
        "match_pct":        match_pct,
        "matched_keywords": matched_keywords,
    })

# Sort by score descending
results.sort(key=lambda x: x["score"], reverse=True)

print(f"Scoring complete")

# ==============================================
# SAVE RANKED CSV
# ==============================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(RANKED_OUTPUT, "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["rank", "company", "title", "location", "salary_range",
                     "score", "match_pct", "top_keywords", "url", "package_folder"])
    for i, r in enumerate(results, 1):
        top_keywords = ", ".join(
            f"{k}({v})" for k, v in
            sorted(r["matched_keywords"].items(), key=lambda x: -x[1])[:5]
        )
        writer.writerow([
            i,
            r["company"],
            r["title"],
            r["location"],
            r["salary_range"],
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
report_lines.append(f"Jobs scored: {len(results)}")
report_lines.append(f"Max possible score: {sum(w for _, w, _ in KEYWORDS)}")
report_lines.append("")

for i, r in enumerate(results, 1):
    report_lines.append(f"#{i}  {r['company']} | {r['title']}")
    report_lines.append(f"    Location: {r['location']}  |  Salary: {r['salary_range']}")
    report_lines.append(f"    Score: {r['score']} ({r['match_pct']}% match)")
    report_lines.append(f"    Matched keywords:")
    for kw, wt in sorted(r["matched_keywords"].items(), key=lambda x: -x[1]):
        report_lines.append(f"      + {kw} ({wt})")
    report_lines.append("")

report_lines.append("=" * 60)

report_text = "\n".join(report_lines)
print("\n" + report_text)

# Save report
with open(REPORT_OUTPUT, "w", encoding='utf-8') as f:
    f.write(report_text)

print(f"\nReport saved to: {REPORT_OUTPUT}")