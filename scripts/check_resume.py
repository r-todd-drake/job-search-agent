# ==============================================
# check_resume.py
# Pre-submission resume quality check.
# Scans a .docx file for known rule violations
# and flags them for review before submitting.
# ==============================================
# Usage:
#   python scripts/check_resume.py resumes/tailored/Leidos_NGLDM/Leidos_NGLDM_SrSE_Resume.docx
# ==============================================
 
import sys
import os
from docx import Document
 
# ==============================================
# RULES
# Each rule is a dict with:
#   name        – short label
#   type        – "contains" or "exact"
#   pattern     – string to search for
#   message     – what to tell the user
#   severity    – "ERROR" or "WARNING"
# ==============================================
 
RULES = [
 
    # ── FORMATTING ──────────────────────────────────────────────────────────
    {
        "name": "Em dash",
        "type": "contains",
        "pattern": "\u2014",
        "message": "Em dash found (\u2014) – replace with en dash (\u2013). Em dashes signal AI-generated content.",
        "severity": "ERROR"
    },
 
    # ── BANNED METRICS ───────────────────────────────────────────────────────
    {
        "name": "Banned metric: cut rework 15%",
        "type": "contains",
        "pattern": "cut rework by 15",
        "message": "Banned metric – unverifiable SWAG. Remove entirely.",
        "severity": "ERROR"
    },
    {
        "name": "Banned metric: reduced delays 30%",
        "type": "contains",
        "pattern": "reduced program delays by 30",
        "message": "Banned metric – unverifiable SWAG. Remove entirely.",
        "severity": "ERROR"
    },
    {
        "name": "Banned metric: test efficiency 30%",
        "type": "contains",
        "pattern": "integration testing efficiency by 30",
        "message": "Banned metric – unverifiable SWAG. Remove entirely.",
        "severity": "ERROR"
    },
    {
        "name": "Banned metric: interoperability 50%",
        "type": "contains",
        "pattern": "interoperability by 50",
        "message": "Banned metric – unverifiable SWAG. Remove entirely.",
        "severity": "ERROR"
    },
    {
        "name": "Banned metric: backlog refinement 25%",
        "type": "contains",
        "pattern": "backlog refinement time by 25",
        "message": "Banned metric – unverifiable SWAG. Remove entirely.",
        "severity": "ERROR"
    },
    {
        "name": "Banned metric: test readiness 3 weeks",
        "type": "contains",
        "pattern": "test readiness by 3 weeks",
        "message": "Banned metric – unverifiable SWAG. Remove entirely.",
        "severity": "ERROR"
    },
    {
        "name": "Banned metric: delivery predictability 15%",
        "type": "contains",
        "pattern": "delivery predictability by 15",
        "message": "Banned metric – unverifiable SWAG. Remove entirely.",
        "severity": "ERROR"
    },
 
    # ── BANNED TERMS ─────────────────────────────────────────────────────────
    {
        "name": "Banned term: airworthiness",
        "type": "contains",
        "pattern": "airworthiness",
        "message": "Saronic builds maritime vessels, NOT aircraft. Remove airworthiness references.",
        "severity": "ERROR"
    },
    {
        "name": "Banned term: Plank Holder",
        "type": "contains",
        "pattern": "Plank Holder",
        "message": "Wrong term – use 'Plank Owner' (two words, capitalized).",
        "severity": "ERROR"
    },
    {
        "name": "Banned term: plank holder lowercase",
        "type": "contains",
        "pattern": "plank holder",
        "message": "Wrong term – use 'Plank Owner' (two words, capitalized).",
        "severity": "ERROR"
    },
    {
        "name": "Banned term: Plankowner one word",
        "type": "contains",
        "pattern": "Plankowner",
        "message": "Non-preferred form – use 'Plank Owner' (two words, capitalized).",
        "severity": "WARNING"
    },
    {
        "name": "Banned term: conformity analysis",
        "type": "contains",
        "pattern": "conformity analysis",
        "message": "Inaccurate term for KForce work – use V/V matrix management and requirements harmonization framing.",
        "severity": "ERROR"
    },
    {
        "name": "Banned term: conformity inspection",
        "type": "contains",
        "pattern": "conformity inspection",
        "message": "Inaccurate term for KForce work – use V/V matrix management framing.",
        "severity": "ERROR"
    },
    {
        "name": "Banned term: safety-critical",
        "type": "contains",
        "pattern": "safety-critical",
        "message": "Aspirational overreach – use 'mission-critical' instead.",
        "severity": "ERROR"
    },
    {
        "name": "Banned term: FEA/CFD",
        "type": "contains",
        "pattern": "FEA/CFD",
        "message": "Overreach – use 'engineering analysis and simulation environments' instead.",
        "severity": "ERROR"
    },
    {
        "name": "Banned term: Terraform",
        "type": "contains",
        "pattern": "Terraform",
        "message": "No Terraform experience – remove from cloud-native framing.",
        "severity": "ERROR"
    },
    {
        "name": "Banned term: managing technical budgets",
        "type": "contains",
        "pattern": "managing technical budgets",
        "message": "Inaccurate – Todd managed workforce/staffing resources, not technical dollars. Use 'managing workforce resources'.",
        "severity": "ERROR"
    },
    {
        "name": "Banned term: white papers",
        "type": "contains",
        "pattern": "white papers",
        "message": "G2 OPS work was internal position papers only – use 'internal technical analyses and position papers'.",
        "severity": "WARNING"
    },
    {
        "name": "Banned term: system software architectures",
        "type": "contains",
        "pattern": "system software architectures",
        "message": "Overreach – use 'software elements within system architecture' instead.",
        "severity": "ERROR"
    },
 
    # ── CLEARANCE TERMINOLOGY ────────────────────────────────────────────────
    {
        "name": "Clearance: Active TS/SCI",
        "type": "contains",
        "pattern": "Active TS/SCI",
        "message": "Clearance terminology: use 'Current TS/SCI' when between employers. Only use 'Active' when employed on a program.",
        "severity": "WARNING"
    },
 
    # ── SHIELD AI HAZARD ANALYSIS ────────────────────────────────────────────
    {
        "name": "Shield AI: leading FHA",
        "type": "contains",
        "pattern": "leading FHA",
        "message": "Shield AI hazard analysis was a supporting role only – do not imply leading FHA/SSA/PSSA.",
        "severity": "ERROR"
    },
    {
        "name": "Shield AI: led FHA",
        "type": "contains",
        "pattern": "led FHA",
        "message": "Shield AI hazard analysis was a supporting role only – do not imply leading FHA/SSA/PSSA.",
        "severity": "ERROR"
    },
]
 
# ==============================================
# SCAN FUNCTION
# ==============================================
 
def check_resume(filepath):
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)
 
    if not filepath.endswith('.docx'):
        print(f"ERROR: File must be a .docx file: {filepath}")
        sys.exit(1)
 
    print(f"\n{'=' * 60}")
    print(f"RESUME QUALITY CHECK")
    print(f"{'=' * 60}")
    print(f"File: {filepath}")
    print(f"Rules: {len(RULES)}")
    print(f"{'=' * 60}\n")
 
    doc = Document(filepath)
 
    # Extract all text with paragraph context
    paragraphs = []
    for i, para in enumerate(doc.paragraphs):
        if para.text.strip():
            paragraphs.append((i + 1, para.text))
 
    errors = []
    warnings = []
 
    for rule in RULES:
        pattern = rule["pattern"].lower()
        for para_num, para_text in paragraphs:
            if pattern in para_text.lower():
                finding = {
                    "rule": rule["name"],
                    "severity": rule["severity"],
                    "message": rule["message"],
                    "paragraph": para_num,
                    "context": para_text[:120] + ("..." if len(para_text) > 120 else "")
                }
                if rule["severity"] == "ERROR":
                    errors.append(finding)
                else:
                    warnings.append(finding)
                break  # Only flag each rule once per document
 
    # Print results
    if not errors and not warnings:
        print("✓ ALL CHECKS PASSED – No issues found.\n")
    else:
        if errors:
            print(f"ERRORS ({len(errors)}) – Must fix before submitting:")
            print("-" * 60)
            for e in errors:
                print(f"\n[ERROR] {e['rule']}")
                print(f"  → {e['message']}")
                print(f"  Paragraph {e['paragraph']}: {e['context']}")
 
        if warnings:
            print(f"\nWARNINGS ({len(warnings)}) – Review before submitting:")
            print("-" * 60)
            for w in warnings:
                print(f"\n[WARNING] {w['rule']}")
                print(f"  → {w['message']}")
                print(f"  Paragraph {w['paragraph']}: {w['context']}")
 
    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {len(errors)} error(s), {len(warnings)} warning(s)")
    if errors:
        print(f"STATUS: FAIL – Fix errors before submitting")
    elif warnings:
        print(f"STATUS: REVIEW – Check warnings before submitting")
    else:
        print(f"STATUS: PASS – Ready to submit")
    print(f"{'=' * 60}\n")
 
    return len(errors), len(warnings)
 
# ==============================================
# MAIN
# ==============================================
 
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_resume.py <path_to_resume.docx>")
        print("Example: python scripts/check_resume.py resumes/tailored/Leidos_NGLDM/Leidos_NGLDM_SrSE_Resume.docx")
        sys.exit(1)
 
    filepath = sys.argv[1]
    errors, warnings = check_resume(filepath)
 
    # Exit with error code if errors found (useful for automation later)
    sys.exit(1 if errors > 0 else 0)