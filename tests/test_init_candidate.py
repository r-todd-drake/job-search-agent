# tests/test_init_candidate.py

import pytest
from pathlib import Path


def test_collect_education_single_degree(monkeypatch):
    # Responses: institution, degree, notes, add_another=n, skip_cont_ed, skip_not_held
    responses = iter(["State University", "B.S. Engineering", "ROTC", "n", "", ""])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.init_candidate import collect_education
    result = collect_education()

    assert result["degrees"] == [
        {"institution": "State University", "degree": "B.S. Engineering", "notes": "ROTC"}
    ]
    assert result["continuing_education"] == []
    assert result["not_held_labels"] == []


def test_collect_education_two_degrees(monkeypatch):
    # First degree, add another, second degree, stop
    responses = iter([
        "State U", "B.S. Engineering", "",  # degree 1
        "y",                                  # add another
        "Tech U", "M.S. Systems", "",         # degree 2
        "n",                                  # stop
        "",                                   # skip cont ed
        "",                                   # skip not_held
    ])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.init_candidate import collect_education
    result = collect_education()

    assert len(result["degrees"]) == 2
    assert result["degrees"][1]["institution"] == "Tech U"


def test_collect_education_with_continuing_ed(monkeypatch):
    responses = iter([
        "State U", "B.S.", "",   # degree
        "n",                      # no more degrees
        "Online Academy", "Data Science Certificate", "completed",  # cont ed
        "",                       # stop cont ed
        "",                       # no not_held
    ])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.init_candidate import collect_education
    result = collect_education()

    assert result["continuing_education"] == [
        {"institution": "Online Academy", "program": "Data Science Certificate", "status": "completed"}
    ]


def test_collect_education_with_not_held_labels(monkeypatch):
    responses = iter([
        "State U", "B.S.", "", "n",  # one degree, stop
        "",                           # skip cont ed
        "Computer Science degree",    # not held label
        "",                           # stop not held
    ])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.init_candidate import collect_education
    result = collect_education()

    assert result["not_held_labels"] == ["Computer Science degree"]


def test_collect_certifications_basic(monkeypatch):
    # active certs (2 then empty), no lapsed, no not_held
    responses = iter([
        "ICAgile Certified Professional",   # active cert 1
        "AWS Solutions Architect",          # active cert 2
        "",                                 # stop active
        "",                                 # no lapsed
        "",                                 # no not_held
    ])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.init_candidate import collect_certifications
    result = collect_certifications()

    assert result["active"] == ["ICAgile Certified Professional", "AWS Solutions Architect"]
    assert result["lapsed"] == []
    assert result["not_held"] == []


def test_collect_certifications_with_lapsed(monkeypatch):
    responses = iter([
        "",          # no active certs
        "CompTIA Security+",  # lapsed cert
        "",                   # stop lapsed
        "",                   # no not_held
    ])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.init_candidate import collect_certifications
    result = collect_certifications()

    assert result["lapsed"] == ["CompTIA Security+"]


def test_collect_military_skipped(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _="": "n")

    from scripts.init_candidate import collect_military
    result = collect_military()

    assert result == {"service": []}


def test_collect_military_one_entry(monkeypatch):
    responses = iter(["y", "U.S. Army", "11B (Infantryman)", "1991–1994", "Airborne", "n"])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.init_candidate import collect_military
    result = collect_military()

    assert result["service"] == [
        {"branch": "U.S. Army", "mos": "11B (Infantryman)",
         "dates": "1991–1994", "notes": "Airborne"}
    ]


def test_collect_clearance_skipped(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _="": "n")

    from scripts.init_candidate import collect_clearance
    result = collect_clearance()

    assert result == {}


def test_collect_clearance_present(monkeypatch):
    responses = iter(["y", "TS/SCI", "Current", "2018"])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.init_candidate import collect_clearance
    result = collect_clearance()

    assert result == {"level": "TS/SCI", "status": "Current", "granted": "2018"}


def test_collect_skills_basic(monkeypatch):
    responses = iter([
        "Python and shell scripting for automation",  # programming description
        "Git/GitHub",                                  # tool 1
        "VS Code",                                     # tool 2
        "",                                            # stop tools
        "Kubernetes",                                  # not_held 1
        "",                                            # stop not_held
    ])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.init_candidate import collect_skills
    result = collect_skills()

    assert result["programming"] == "Python and shell scripting for automation"
    assert result["tools"] == ["Git/GitHub", "VS Code"]
    assert result["not_held"] == ["Kubernetes"]


def test_collect_gaps_two_entries(monkeypatch):
    responses = iter([
        "No Kubernetes or container orchestration experience.",
        "No formal PMI project management certification.",
        "",
    ])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.init_candidate import collect_gaps
    result = collect_gaps()

    assert len(result) == 2
    assert result[0] == "No Kubernetes or container orchestration experience."


def test_collect_employers_two_entries(monkeypatch):
    responses = iter([
        "Acme Corp", "1",  # employer 1, tier 1
        "y",               # add another
        "Beta Inc", "2",   # employer 2, tier 2
        "n",               # stop
    ])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.init_candidate import collect_employers
    result = collect_employers()

    assert result == [
        {"name": "Acme Corp", "tier": 1},
        {"name": "Beta Inc", "tier": 2},
    ]


def test_collect_resume_defaults(monkeypatch):
    responses = iter([
        "Senior Systems Engineer",
        "State University — B.S. Engineering",
        "ICAgile Certified Professional | Current TS/SCI",
    ])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.init_candidate import collect_resume_defaults
    result = collect_resume_defaults()

    assert result["role_title"] == "Senior Systems Engineer"
    assert result["education_line"] == "State University — B.S. Engineering"
    assert result["certifications_line"] == "ICAgile Certified Professional | Current TS/SCI"


def test_collect_style_rules_defaults_only(monkeypatch):
    # User skips the terminology rules question
    monkeypatch.setattr("builtins.input", lambda _="": "n")

    from scripts.init_candidate import collect_style_rules
    result = collect_style_rules()

    assert result["dash_style"] == "en dash only — never em dash"
    assert result["metric_rule"] == "no unverifiable metrics"
    assert result["terminology"] == []


def test_save_config_writes_valid_yaml(tmp_path, monkeypatch):
    import scripts.utils.candidate_config as cc
    config_path = tmp_path / "candidate_config.yaml"

    data = {
        "education": {"degrees": [{"institution": "Test U", "degree": "B.S.", "notes": ""}],
                       "continuing_education": [], "not_held_labels": []},
        "certifications": {"active": [], "lapsed": [], "not_held": []},
        "military": {"service": []},
        "clearance": {},
        "confirmed_skills": {"programming": "Python", "tools": [], "not_held": []},
        "confirmed_gaps": [],
        "employers": [{"name": "Acme Corp", "tier": 1}],
        "resume_defaults": {"role_title": "Engineer", "education_line": "Test U — B.S.",
                             "certifications_line": "None"},
        "style_rules": {"dash_style": "en dash only — never em dash",
                         "metric_rule": "no unverifiable metrics", "terminology": []},
        "intro_monologue": "[placeholder — fill in manually]",
        "short_tenure_explanation": "[placeholder — fill in manually if applicable]",
    }

    from scripts.init_candidate import save_config
    save_config(data, config_path=config_path)

    assert config_path.exists()

    # Confirm the YAML is readable by the loader
    monkeypatch.setattr(cc, "_config", None)
    monkeypatch.setattr("scripts.utils.candidate_config._CONFIG_PATH", str(config_path))
    loaded = cc.load()
    assert loaded["employers"][0]["name"] == "Acme Corp"


def test_save_config_overwrites_existing(tmp_path, monkeypatch):
    import scripts.utils.candidate_config as cc
    config_path = tmp_path / "candidate_config.yaml"
    config_path.write_text("old: content\n")

    data = {
        "education": {"degrees": [], "continuing_education": [], "not_held_labels": []},
        "certifications": {"active": [], "lapsed": [], "not_held": []},
        "military": {"service": []},
        "clearance": {},
        "confirmed_skills": {"programming": "", "tools": [], "not_held": []},
        "confirmed_gaps": [],
        "employers": [],
        "resume_defaults": {"role_title": "", "education_line": "", "certifications_line": ""},
        "style_rules": {"dash_style": "en dash only — never em dash",
                         "metric_rule": "no unverifiable metrics", "terminology": []},
        "intro_monologue": "[placeholder]",
        "short_tenure_explanation": "[placeholder]",
    }

    from scripts.init_candidate import save_config
    save_config(data, config_path=config_path)

    content = config_path.read_text()
    assert "old: content" not in content
    assert "employers" in content


def test_run_wizard_writes_config(tmp_path, monkeypatch):
    import scripts.utils.candidate_config as cc
    config_path = tmp_path / "candidate_config.yaml"
    monkeypatch.setattr("scripts.init_candidate._CONFIG_PATH", config_path)
    monkeypatch.setattr("scripts.utils.candidate_config._CONFIG_PATH", str(config_path))

    # Provide minimal valid responses for all 10 sections
    responses = iter([
        # Education: one degree, no cont ed, no not_held
        "State University", "B.S. Engineering", "", "n", "", "",
        # Certifications: no active, no lapsed, no not_held
        "", "", "",
        # Military: skip
        "n",
        # Clearance: skip
        "n",
        # Skills: programming desc, one tool, one not_held
        "Python scripting", "Git", "", "Kubernetes", "",
        # Gaps: one gap, stop
        "No formal PM certification.", "",
        # Employers: one employer
        "Acme Corp", "1", "n",
        # Resume defaults
        "Senior Engineer", "State U — B.S.", "Cert Line",
        # Style rules: no terminology
        "n",
    ])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.init_candidate import run_wizard
    run_wizard()

    monkeypatch.setattr(cc, "_config", None)
    loaded = cc.load()
    assert loaded["employers"] == [{"name": "Acme Corp", "tier": 1}]
    assert loaded["education"]["degrees"][0]["institution"] == "State University"
    assert loaded["intro_monologue"] == "[placeholder — fill in manually]"


def test_main_exits_when_example_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.init_candidate._EXAMPLE_PATH",
                        tmp_path / "missing_example.yaml")

    from scripts.init_candidate import main
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
