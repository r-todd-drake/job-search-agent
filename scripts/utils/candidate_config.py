import os
import yaml
from dotenv import load_dotenv

_CONFIG_PATH = "context/candidate/candidate_config.yaml"
_config = None


def load():
    global _config
    if _config is None:
        if not os.path.exists(_CONFIG_PATH):
            raise FileNotFoundError(
                f"{_CONFIG_PATH} not found. "
                f"Copy context/candidate/candidate_config.example.yaml, "
                f"fill in your data, and save as candidate_config.yaml."
            )
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            _config = yaml.safe_load(f)
    return _config


def get_hardcoded_rules(document_type="resume"):
    """Return HARDCODED_RULES as a list of (rule_name, pattern, fix, case_sensitive) tuples.

    The em dash rule is universal and hardcoded here. All other rules come from
    style_rules in candidate_config.yaml.
    """
    cfg = load()
    rules = []

    rules.append((
        "Em dash",
        "—",
        "Replace — with – (en dash)",
        True,
    ))

    style = cfg.get("style_rules", {})

    for cert in style.get("lapsed_certs_to_exclude", []):
        rules.append((
            f"{cert['name']} reference",
            cert["name"],
            f"{cert['fix']} on {document_type}",
            False,
        ))

    cl = style.get("clearance_language", {})
    if cl.get("pattern_to_flag"):
        rules.append((
            cl["pattern_to_flag"],
            cl["pattern_to_flag"],
            cl["fix"],
            True,
        ))

    for term in style.get("terminology", []):
        rules.append((
            term.get("rule_name", term["pattern"]),
            term["pattern"],
            f"Use '{term['replacement']}' instead",
            term.get("case_sensitive", False),
        ))

    return rules


def build_known_facts():
    """Build the KNOWN_FACTS text block for Claude prompts in phase3.

    Combines scalar PII from .env with structured career data from candidate_config.yaml.
    """
    load_dotenv()
    cfg = load()

    lines = ["\nCONFIRMED FACTS (supplement library data):"]
    lines.append(f"- Name: {os.getenv('CANDIDATE_NAME', '[CANDIDATE]')}")
    lines.append(f"- Location: {os.getenv('CANDIDATE_LOCATION', '[LOCATION]')}")
    lines.append(f"- Phone: {os.getenv('CANDIDATE_PHONE', '[PHONE]')}")
    lines.append(f"- Email: {os.getenv('CANDIDATE_EMAIL', '[EMAIL]')}")
    lines.append(f"- LinkedIn: {os.getenv('CANDIDATE_LINKEDIN', '[LINKEDIN]')}")
    lines.append(f"- GitHub: {os.getenv('CANDIDATE_GITHUB', '[GITHUB]')}")
    lines.append("")

    edu = cfg.get("education", {})
    lines.append("EDUCATION (confirmed):")
    for deg in edu.get("degrees", []):
        lines.append(f"- {deg.get('institution', '')}")
        lines.append(f"- Degree: {deg.get('degree', '')}")
        if deg.get("notes"):
            lines.append(f"- {deg['notes']}")
    for entry in edu.get("continuing_education", []):
        lines.append(f"- {entry.get('institution', '')} — {entry.get('program', '')} ({entry.get('status', '')})")
    for label in edu.get("not_held_labels", []):
        lines.append(f"- NOT a {label}")
    lines.append("")

    certs = cfg.get("certifications", {})
    lines.append("CERTIFICATIONS (confirmed):")
    for cert in certs.get("active", []):
        lines.append(f"- {cert}")
    for cert in certs.get("lapsed", []):
        lines.append(f"- {cert} (lapsed)")
    for cert in certs.get("not_held", []):
        lines.append(f"- NOT {cert}")
    lines.append("")

    cl = cfg.get("clearance", {})
    style = cfg.get("style_rules", {})
    cl_lang = style.get("clearance_language", {})
    lines.append("CLEARANCE:")
    lines.append(f"- {cl.get('status', 'Current')} {cl.get('level', 'TS/SCI')} (granted {cl.get('granted', '')})")
    if cl_lang.get("between_employers"):
        lines.append(f"- Use \"{cl_lang['between_employers']}\" when between employers")
        lines.append(f"- Use \"{cl_lang['on_program']}\" once employed on a program")
    lines.append("")

    mil = cfg.get("military", {})
    lines.append("MILITARY SERVICE (confirmed):")
    for svc in mil.get("service", []):
        entry = f"- {svc.get('branch', '')} {svc.get('mos', '')} {svc.get('dates', '')}".strip()
        lines.append(entry)
        if svc.get("notes"):
            lines.append(f"- {svc['notes']}")
    lines.append("")

    skills = cfg.get("confirmed_skills", {})
    lines.append("CONFIRMED SKILLS - PROGRAMMING:")
    lines.append(f"- {skills.get('programming', '')}")
    for tool in skills.get("tools", []):
        lines.append(f"- {tool}")
    for item in skills.get("not_held", []):
        lines.append(f"- No {item}")
    lines.append("")

    lines.append("CONFIRMED GAPS (never include on resume):")
    for gap in cfg.get("confirmed_gaps", []):
        lines.append(f"- {gap}")
    lines.append("")

    lines.append("STYLE RULES:")
    lines.append(f"- {style.get('dash_style', 'En dashes only, never em dashes')}")
    lines.append(f"- {style.get('metric_rule', 'No unverifiable metrics')}")
    for term in style.get("terminology", []):
        lines.append(f"- \"{term['pattern']}\" not \"{term['replacement']}\"")

    return "\n".join(lines)
