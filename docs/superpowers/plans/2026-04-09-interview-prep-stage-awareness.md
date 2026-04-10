# Phase 5 Interview Stage Awareness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `--interview_stage` (recruiter / hiring_manager / team_panel) to `phase5_interview_prep.py`, driving stage-specific behavior across all five output sections plus a new "Introduce Yourself" section, with `--dry_run` support.

**Architecture:** A `STAGE_PROFILES` dict at module level holds all stage-specific settings and prompt templates. `generate_prep()` resolves the active profile from the stage string and passes it to each section's prompt builder. Stage-specific candidate content (intro monologue, short tenure explanation) is extracted from `candidate_profile.md` by header name at runtime — no personal content or company names hardcoded in the script.

**Tech Stack:** Python 3, anthropic SDK, python-docx, pytest, unittest.mock

---

## File Map

| File | Action | What changes |
|---|---|---|
| `scripts/phase5_interview_prep.py` | Modify | Stage profiles, new helpers, parameterized prompts, conditional section logic, updated docx |
| `tests/phase5/test_interview_prep.py` | Modify | Update all existing tests for new signature; add 9 new tests |
| `tests/fixtures/library/candidate_profile.md` | Modify | Add INTRO MONOLOGUE and SHORT TENURE EXPLANATION sections |

---

## Task 1: Add STAGE_PROFILES and prompt constants to script

**Files:**
- Modify: `scripts/phase5_interview_prep.py` (after `SYSTEM_PROMPT` block, before `extract_salary`)

- [ ] **Step 1: Write failing test for stage profile structure**

Add to `tests/phase5/test_interview_prep.py`:

```python
def test_stage_profile_has_required_keys():
    from scripts.phase5_interview_prep import STAGE_PROFILES, VALID_STAGES

    required_keys = {
        "label", "description", "story_count", "story_depth",
        "gap_behavior", "salary_in_section1", "section1_focus", "questions_prompt",
    }
    assert set(VALID_STAGES) == {"recruiter", "hiring_manager", "team_panel"}
    for stage, profile in STAGE_PROFILES.items():
        missing = required_keys - profile.keys()
        assert not missing, f"Stage '{stage}' missing keys: {missing}"
    assert "peer_frame_prompt" in STAGE_PROFILES["team_panel"]
    assert STAGE_PROFILES["recruiter"]["gap_behavior"] == "omit"
    assert STAGE_PROFILES["hiring_manager"]["salary_in_section1"] is True
    assert STAGE_PROFILES["team_panel"]["story_depth"] == "full_technical"
```

- [ ] **Step 2: Run test to confirm it fails**

```
pytest tests/phase5/test_interview_prep.py::test_stage_profile_has_required_keys -v
```
Expected: FAIL — `cannot import name 'STAGE_PROFILES'`

- [ ] **Step 3: Add constants and STAGE_PROFILES to script**

Insert after the `SYSTEM_PROMPT` block (after line 75) in `scripts/phase5_interview_prep.py`:

```python
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
- The hiring manager's vision for the MBSE or architecture effort going forward

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
        "description": "Short screen -- confirm fit, do not volunteer gaps or technical depth.",
        "story_count": "1-2",
        "story_depth": "headline",
        "gap_behavior": "omit",
        "salary_in_section1": False,
        "section1_focus": "recruiter",
        "questions_prompt": _QUESTIONS_RECRUITER,
    },
    "hiring_manager": {
        "label": "Hiring Manager Interview",
        "description": "60+ min interview -- lead with program context awareness and collaborative framing.",
        "story_count": "3-4",
        "story_depth": "full",
        "gap_behavior": "note",
        "salary_in_section1": True,
        "section1_focus": "hiring_manager",
        "questions_prompt": _QUESTIONS_HIRING_MANAGER,
    },
    "team_panel": {
        "label": "Team Panel Interview",
        "description": "90 min to 3 hr group interview -- lead with technical specificity and process fluency.",
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
```

- [ ] **Step 4: Run test to confirm it passes**

```
pytest tests/phase5/test_interview_prep.py::test_stage_profile_has_required_keys -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "Add STAGE_PROFILES dict and stage prompt constants to phase5_interview_prep"
```

---

## Task 2: Update generate_prep() and generate_prep_docx() signatures; fix existing tests

**Files:**
- Modify: `scripts/phase5_interview_prep.py` (lines 261, 368)
- Modify: `tests/phase5/test_interview_prep.py` (all 6 existing tests)

- [ ] **Step 1: Update existing tests to use new signature**

In `tests/phase5/test_interview_prep.py`, update `MOCK_PREP_RESPONSE` to include an intro section (the mock returns the same text for all API calls, so we just need a neutral response that satisfies all section checks):

```python
MOCK_PREP_RESPONSE = """## SECTION 1: COMPANY & ROLE BRIEF
Acme Defense Systems is a defense contractor focused on autonomous maritime systems.
Role: Senior Systems Engineer supporting MBSE and DoDAF development.
Salary guidance: $150,000 - $180,000.

## SECTION 1.5: INTRODUCE YOURSELF
I am a senior systems engineer with 20 years of defense SE experience.
I specialize in MBSE and DoDAF architectural development.

## SECTION 2: STORY BANK
STAR Story 1 - MBSE Leadership
Situation: Led MBSE development for autonomous surface vessel program.
Task: Develop DoDAF architectural views using Cameo Systems Modeler.
Action: Facilitated IPT working groups with government stakeholders.
Result: Delivered system-of-systems architecture supporting multi-domain C2 integration.

STAR Story 2 - Stakeholder Engagement
Situation: Government stakeholder alignment required for requirements definition.
Task: Define operational requirements and ConOps.
Action: Conducted workshops and facilitated reviews.
Result: Approved ConOps baseline.

STAR Story 3 - Architecture Integration
Situation: System integration complexity.
Task: Develop integration architecture.
Action: Applied DoDAF SV views.
Result: Successful integration milestone.

## SECTION 3: GAP PREPARATION
REQUIRED: All required qualifications met.
PREFERRED: JADC2 experience limited -- acknowledge and reframe.

## SECTION 4: QUESTIONS TO ASK
1. What is the acquisition phase for this program?
2. How is MBSE integrated into the program baseline?
"""
```

Update all 6 existing test functions to add `"hiring_manager"` as the third argument to `generate_prep()`:

```python
# test_generate_prep_creates_both_output_files
generate_prep(client, role_data, "hiring_manager", str(txt_path), str(docx_path))

# test_generate_prep_txt_has_required_sections
generate_prep(client, role_data, "hiring_manager", str(txt_path), str(docx_path))

# test_generate_prep_star_stories_reference_resume_content
generate_prep(client, role_data, "hiring_manager", str(txt_path), str(docx_path))

# test_generate_prep_no_pii_in_api_payload
generate_prep(client, role_data, "hiring_manager", str(txt_path), str(docx_path))

# test_generate_prep_docx_readable
generate_prep(client, role_data, "hiring_manager", str(txt_path), str(docx_path))

# test_generate_prep_live (the @pytest.mark.live test)
generate_prep(client, role_data, "hiring_manager", str(txt_path), str(docx_path))
```

Also update the `txt_path` and `docx_path` variable names in the existing tests to use the stage-specific filename:

```python
txt_path = Path(tmpdir) / "interview_prep_hiring_manager.txt"
docx_path = Path(tmpdir) / "interview_prep_hiring_manager.docx"
```

- [ ] **Step 2: Update generate_prep() signature in script**

Change line 368 in `scripts/phase5_interview_prep.py`:

```python
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
```

Add the profile resolution as the very first line of the function body (before `jd = role_data["jd_text"]`).

- [ ] **Step 3: Update generate_prep_docx() signature**

Change line 261:

```python
def generate_prep_docx(output_path, role, resume_source, stage_profile,
                        section1, section_intro, section2, section3, section4,
                        salary_data):
```

Add `stage_profile` and `section_intro` after `resume_source`. No other changes to the docx function body yet — that comes in Task 12.

For now, update only the title line to show stage. Find the existing title block in the function and update:

```python
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
```

- [ ] **Step 4: Update the generate_prep_docx() call site inside generate_prep()**

Find the call to `generate_prep_docx()` inside `generate_prep()` and update:

```python
generate_prep_docx(
    output_docx_path, role_name, resume_source, profile,
    section1, section_intro, section2, section3, section4,
    salary_data
)
```

(Note: `section_intro` will be added in Task 9 — for now add it as a placeholder empty string `""` in the call so the script remains runnable.)

- [ ] **Step 5: Run existing tests to confirm they all pass**

```
pytest tests/phase5/test_interview_prep.py -v -k "not live"
```
Expected: all 5 non-live tests PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "Update generate_prep/docx signatures for interview_stage; fix existing tests"
```

---

## Task 3: Add CLI arguments and interactive fallback to main()

**Files:**
- Modify: `scripts/phase5_interview_prep.py` (`main()` function)

- [ ] **Step 1: Write failing test for invalid stage validation**

Add to `tests/phase5/test_interview_prep.py`:

```python
def test_invalid_stage_raises_system_exit(monkeypatch):
    import scripts.phase5_interview_prep as mod
    monkeypatch.setattr("sys.argv", ["phase5_interview_prep.py", "--role", "test_role",
                                      "--interview_stage", "badstage"])
    with pytest.raises(SystemExit):
        mod.main()
```

- [ ] **Step 2: Run test to confirm it fails**

```
pytest tests/phase5/test_interview_prep.py::test_invalid_stage_raises_system_exit -v
```
Expected: FAIL — `main()` currently doesn't have `--interview_stage`

- [ ] **Step 3: Update main() argument parser and add validation**

Replace the existing `parser` block in `main()`:

```python
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
        print(f"  {i}. {s} -- {p['label']}: {p['description']}")
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
```

- [ ] **Step 4: Update output path construction in main() to use stage-specific filenames**

Replace the existing `output_txt_path` and `output_docx_path` lines:

```python
output_txt_path = os.path.join(package_dir, f"interview_prep_{interview_stage}.txt")
output_docx_path = os.path.join(package_dir, f"interview_prep_{interview_stage}.docx")
```

Also update the overwrite protection check — it currently uses `OUTPUT_FILENAME`. Replace:

```python
if os.path.exists(output_txt_path):
    print(f"\nWARNING: interview_prep_{interview_stage}.txt already exists.")
    overwrite = input("  Overwrite? (y/n): ").strip().lower()
    if overwrite != 'y':
        print("  Cancelled. Existing file preserved.")
        sys.exit(0)
```

Also pass `interview_stage` to the `generate_prep()` call at the bottom of `main()`:

```python
generate_prep(client, role_data, interview_stage, output_txt_path, output_docx_path)
```

- [ ] **Step 5: Run test to confirm it passes**

```
pytest tests/phase5/test_interview_prep.py::test_invalid_stage_raises_system_exit -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "Add --interview_stage and --dry_run CLI args; interactive stage fallback"
```

---

## Task 4: Implement --dry_run

**Files:**
- Modify: `scripts/phase5_interview_prep.py` (`generate_prep()`)

- [ ] **Step 1: Write failing test**

Add to `tests/phase5/test_interview_prep.py`:

```python
def test_dry_run_no_api_calls():
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep_hiring_manager.txt"
        docx_path = Path(tmpdir) / "interview_prep_hiring_manager.docx"
        generate_prep(client, role_data, "hiring_manager",
                      str(txt_path), str(docx_path), dry_run=True)
        assert not txt_path.exists(), "dry_run must not write output files"

    assert client.messages.create.call_count == 0, "dry_run must make no API calls"
```

- [ ] **Step 2: Run test to confirm it fails**

```
pytest tests/phase5/test_interview_prep.py::test_dry_run_no_api_calls -v
```
Expected: FAIL — dry_run does nothing special yet

- [ ] **Step 3: Add dry_run early return to generate_prep()**

Add immediately after `profile = STAGE_PROFILES[interview_stage]` at the top of `generate_prep()`:

```python
if dry_run:
    print("\nDRY RUN -- Stage profile that will be applied:")
    print(f"  Stage:       {profile['label']}")
    print(f"  Description: {profile['description']}")
    print(f"  Story count: {profile['story_count']}")
    print(f"  Story depth: {profile['story_depth']}")
    print(f"  Gap behavior:{profile['gap_behavior']}")
    print(f"  Salary in S1:{profile['salary_in_section1']}")
    print("\nNo API calls made. No files written.")
    return
```

- [ ] **Step 4: Run test to confirm it passes**

```
pytest tests/phase5/test_interview_prep.py::test_dry_run_no_api_calls -v
```
Expected: PASS

- [ ] **Step 5: Run all phase5 tests to confirm nothing broke**

```
pytest tests/phase5/test_interview_prep.py -v -k "not live"
```
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "Implement --dry_run: print stage profile and exit without API calls"
```

---

## Task 5: Stage-specific filename helper and output header

**Files:**
- Modify: `scripts/phase5_interview_prep.py`
- Modify: `tests/phase5/test_interview_prep.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/phase5/test_interview_prep.py`:

```python
def test_stage_specific_filenames():
    from scripts.phase5_interview_prep import _output_paths
    for stage in ("recruiter", "hiring_manager", "team_panel"):
        txt, docx = _output_paths("/some/dir", stage)
        assert txt.endswith(f"interview_prep_{stage}.txt")
        assert docx.endswith(f"interview_prep_{stage}.docx")


def test_stage_in_output_header():
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep_recruiter.txt"
        docx_path = Path(tmpdir) / "interview_prep_recruiter.docx"
        generate_prep(client, role_data, "recruiter", str(txt_path), str(docx_path))
        content = txt_path.read_text(encoding="utf-8")

    assert "Stage: Recruiter Screen" in content
    assert "Short screen" in content
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/phase5/test_interview_prep.py::test_stage_specific_filenames tests/phase5/test_interview_prep.py::test_stage_in_output_header -v
```
Expected: both FAIL

- [ ] **Step 3: Add _output_paths() helper to script**

Add before `extract_salary()` in `scripts/phase5_interview_prep.py`:

```python
def _output_paths(package_dir, stage):
    """Return (txt_path, docx_path) for the given stage."""
    return (
        os.path.join(package_dir, f"interview_prep_{stage}.txt"),
        os.path.join(package_dir, f"interview_prep_{stage}.docx"),
    )
```

Update `main()` to use this helper. Replace the two `output_txt_path`/`output_docx_path` lines:

```python
output_txt_path, output_docx_path = _output_paths(package_dir, interview_stage)
```

- [ ] **Step 4: Add stage info to output header in generate_prep()**

Find the header block in `generate_prep()` (the `output_lines` section) and add after the `Resume source` line:

```python
output_lines.append(f"Stage: {profile['label']}")
output_lines.append(f"Stage note: {profile['description']}")
```

- [ ] **Step 5: Run tests to confirm both pass**

```
pytest tests/phase5/test_interview_prep.py::test_stage_specific_filenames tests/phase5/test_interview_prep.py::test_stage_in_output_header -v
```
Expected: both PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "Add _output_paths helper; stage label and description in output header"
```

---

## Task 6: Add extract_profile_section() helper

**Files:**
- Modify: `scripts/phase5_interview_prep.py`
- Modify: `tests/phase5/test_interview_prep.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/phase5/test_interview_prep.py`:

```python
def test_extract_profile_section_found():
    from scripts.phase5_interview_prep import extract_profile_section
    text = "## INTRO MONOLOGUE\nHello world.\n## OTHER SECTION\nOther content."
    result = extract_profile_section(text, "INTRO MONOLOGUE")
    assert "Hello world" in result
    assert "OTHER SECTION" not in result


def test_extract_profile_section_missing():
    from scripts.phase5_interview_prep import extract_profile_section
    result = extract_profile_section("## OTHER SECTION\nStuff.", "INTRO MONOLOGUE")
    assert result == ""


def test_extract_profile_section_last_section():
    from scripts.phase5_interview_prep import extract_profile_section
    text = "## SHORT TENURE EXPLANATION\nI left because the contract ended."
    result = extract_profile_section(text, "SHORT TENURE EXPLANATION")
    assert "contract ended" in result
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/phase5/test_interview_prep.py::test_extract_profile_section_found tests/phase5/test_interview_prep.py::test_extract_profile_section_missing tests/phase5/test_interview_prep.py::test_extract_profile_section_last_section -v
```
Expected: all FAIL — `cannot import name 'extract_profile_section'`

- [ ] **Step 3: Add helper to script**

Add after `_output_paths()` in `scripts/phase5_interview_prep.py`:

```python
def extract_profile_section(profile_text, header):
    """
    Extract a ## HEADER section from candidate_profile.md text.
    Returns the section body (stripped), or empty string if header not found.
    """
    marker = f"## {header}"
    if marker not in profile_text:
        return ""
    start = profile_text.find(marker) + len(marker)
    next_header = profile_text.find("\n## ", start)
    end = next_header if next_header > 0 else len(profile_text)
    return profile_text[start:end].strip()
```

- [ ] **Step 4: Run tests to confirm all three pass**

```
pytest tests/phase5/test_interview_prep.py::test_extract_profile_section_found tests/phase5/test_interview_prep.py::test_extract_profile_section_missing tests/phase5/test_interview_prep.py::test_extract_profile_section_last_section -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "Add extract_profile_section() helper and tests"
```

---

## Task 7: Add fixture headers for intro monologue and short tenure

**Files:**
- Modify: `tests/fixtures/library/candidate_profile.md`

- [ ] **Step 1: Add new headers to test fixture**

Append to `tests/fixtures/library/candidate_profile.md`:

```markdown

## INTRO MONOLOGUE
I am a senior systems engineer with over 20 years of experience in defense and aerospace programs. My background spans MBSE development, DoDAF architecture, and systems integration for autonomous and C2 programs. I bring both technical depth in Cameo Systems Modeler and stakeholder engagement experience working with government program offices.

## SHORT TENURE EXPLANATION
I joined to support a specific program opportunity that was subsequently restructured before I could make an impact. The role ended when the contract scope changed -- not a performance issue. I learned a great deal about rapid program standup in a startup environment and remain proud of the work I contributed during that time.
```

- [ ] **Step 2: Verify the fixture is readable**

```
pytest tests/phase5/test_interview_prep.py -v -k "not live"
```
Expected: all existing tests still PASS (no regressions from fixture change)

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/library/candidate_profile.md
git commit -m "Add INTRO MONOLOGUE and SHORT TENURE EXPLANATION to test fixture profile"
```

---

## Task 8: Parameterize Section 1 prompt by stage

**Files:**
- Modify: `scripts/phase5_interview_prep.py`

- [ ] **Step 1: Write failing test**

Add to `tests/phase5/test_interview_prep.py`:

```python
def test_section1_salary_only_for_hiring_manager():
    from scripts.phase5_interview_prep import generate_prep

    # hiring_manager — salary should appear in the API call payload
    client_hm = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()
    with tempfile.TemporaryDirectory() as tmpdir:
        generate_prep(client_hm, role_data, "hiring_manager",
                      str(Path(tmpdir) / "interview_prep_hiring_manager.txt"),
                      str(Path(tmpdir) / "interview_prep_hiring_manager.docx"))

    hm_calls = client_hm.messages.create.call_args_list
    section1_call = str(hm_calls[0])
    assert "salary" in section1_call.lower() or "SALARY" in section1_call

    # recruiter — salary should NOT appear in the Section 1 API call payload
    client_rec = make_mock_client(MOCK_PREP_RESPONSE)
    with tempfile.TemporaryDirectory() as tmpdir:
        generate_prep(client_rec, role_data, "recruiter",
                      str(Path(tmpdir) / "interview_prep_recruiter.txt"),
                      str(Path(tmpdir) / "interview_prep_recruiter.docx"))

    rec_calls = client_rec.messages.create.call_args_list
    section1_rec_call = str(rec_calls[0])
    assert "SALARY EXPECTATIONS GUIDANCE" not in section1_rec_call
```

- [ ] **Step 2: Run test to confirm it fails**

```
pytest tests/phase5/test_interview_prep.py::test_section1_salary_only_for_hiring_manager -v
```
Expected: FAIL

- [ ] **Step 3: Add _build_section1_prompt() helper and refactor Section 1 in generate_prep()**

Add after `extract_profile_section()` in the script:

```python
def _build_section1_prompt(jd, salary_data, profile):
    """Build the Section 1 company brief prompt, parameterized by stage profile."""
    _stage_instructions = {
        "recruiter": (
            "Focus on:\n"
            "- Company overview (3-4 sentences): what they do, defense/government focus, scale\n"
            "- Culture signals: what employees say about the environment and retention\n"
            "- Recent news: contracts, programs, or announcements relevant to this role\n"
            "- Interview process context: who typically interviews next, what they evaluate\n"
            "Omit salary guidance. Do not include detailed program or technical content."
        ),
        "hiring_manager": (
            "Focus on:\n"
            "- Full company overview (3-4 sentences): mission, defense/government business, scale\n"
            "- Business unit deep-dive (2-3 sentences): specific unit, programs, stakeholders\n"
            "- Program pain points: based on JD language, what problems is this role solving?\n"
            "- Role in context: day-to-day responsibilities inferred from JD\n"
            "Include salary guidance block."
        ),
        "team_panel": (
            "Focus on:\n"
            "- Company overview: CONDENSED to 2-3 sentences -- panel members know the company\n"
            "- Program-specific context: mission area, technical environment, active programs from JD\n"
            "- Technical environment: tools, methodologies, and stack signals in JD language\n"
            "Omit salary guidance. Omit general culture content."
        ),
    }

    salary_block = ""
    if profile["salary_in_section1"]:
        salary_block = (
            f"\nSALARY & LEVEL CONTEXT:\n"
            f"JD posted range: {salary_data['text'] if salary_data['found'] else 'Not found in JD'}\n"
            f"[1-2 sentences on what level this represents and where initial offers land.]\n\n"
            f"SALARY EXPECTATIONS GUIDANCE:\n"
            f"{salary_data['guidance'] if salary_data['found'] else 'Research market rate before interview.'}\n"
        )

    return (
        f"Research this company and role, then generate an interview prep brief "
        f"for a {profile['label']}.\n\n"
        f"JOB DESCRIPTION:\n{jd[:2500]}\n\n"
        f"Use the web_search tool to find current information about this company.\n\n"
        f"Stage-specific instructions:\n{_stage_instructions[profile['section1_focus']]}\n"
        f"{salary_block}\n"
        f"Format your brief with ALL-CAPS section headers followed by a colon "
        f"(e.g., 'COMPANY OVERVIEW:'). Include only sections relevant to this stage."
    )
```

In `generate_prep()`, replace the `company_prompt = f"""..."""` block with:

```python
company_prompt = _build_section1_prompt(jd, salary_data, profile)
```

- [ ] **Step 4: Run test to confirm it passes**

```
pytest tests/phase5/test_interview_prep.py::test_section1_salary_only_for_hiring_manager -v
```
Expected: PASS

- [ ] **Step 5: Run all phase5 tests**

```
pytest tests/phase5/test_interview_prep.py -v -k "not live"
```
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "Parameterize Section 1 prompt by stage; salary only for hiring_manager"
```

---

## Task 9: Add Section 1.5 — Introduce Yourself

**Files:**
- Modify: `scripts/phase5_interview_prep.py`
- Modify: `tests/phase5/test_interview_prep.py`

- [ ] **Step 1: Write failing test**

Add to `tests/phase5/test_interview_prep.py`:

```python
def test_intro_monologue_in_output():
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep_hiring_manager.txt"
        docx_path = Path(tmpdir) / "interview_prep_hiring_manager.docx"
        generate_prep(client, role_data, "hiring_manager", str(txt_path), str(docx_path))
        content = txt_path.read_text(encoding="utf-8")

    assert "INTRODUCE YOURSELF" in content or "SECTION 1.5" in content
```

- [ ] **Step 2: Run test to confirm it fails**

```
pytest tests/phase5/test_interview_prep.py::test_intro_monologue_in_output -v
```
Expected: FAIL

- [ ] **Step 3: Add _build_intro_prompt() helper**

Add after `_build_section1_prompt()` in the script:

```python
def _build_intro_prompt(intro_monologue, profile):
    """Build the 'Introduce Yourself' tailoring prompt, parameterized by stage profile."""
    _tailoring = {
        "recruiter": (
            "2-3 sentences, high-level",
            "overall fit and interest in the role -- confirm you are not a risk",
        ),
        "hiring_manager": (
            "3-4 sentences, program-context aware",
            "program experience, collaborative working style, and why this problem interests you",
        ),
        "team_panel": (
            "4-5 sentences, technically grounded",
            "specific tools, methodologies, and day-to-day peer-relevant experience",
        ),
    }
    length_guidance, emphasis = _tailoring[profile["section1_focus"]]

    return (
        f"The candidate has a prepared introduction for 'Tell me about yourself.'\n\n"
        f"BASE INTRODUCTION:\n{intro_monologue}\n\n"
        f"Tailor this introduction for a {profile['label']} interview.\n"
        f"- Length: {length_guidance}\n"
        f"- Emphasis: {emphasis}\n"
        f"- Register: appropriate for this audience ({profile['description']})\n\n"
        f"Rules:\n"
        f"- Keep all factual content present in the base text\n"
        f"- Do not add experience, credentials, or claims not in the base text\n"
        f"- Return the tailored introduction as flowing prose (1-2 short paragraphs max)\n"
        f"- Do not add headers or labels -- return only the introduction text itself"
    )
```

- [ ] **Step 4: Add Section 1.5 API call and output section in generate_prep()**

After the Section 1 API call block (after `section1 = ...`) and before Section 2, add:

```python
# --------------------------------------------------
# SECTION 1.5 -- INTRODUCE YOURSELF
# --------------------------------------------------
print("Section 1.5: Introduce Yourself (tailoring for stage)...")

raw_intro = extract_profile_section(raw_profile, "INTRO MONOLOGUE")
if raw_intro:
    intro_prompt = _build_intro_prompt(strip_pii(raw_intro), profile)
    response_intro = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": intro_prompt}]
    )
    section_intro = response_intro.content[0].text
else:
    section_intro = (
        "No INTRO MONOLOGUE section found in candidate_profile.md. "
        "Add one to enable stage-tailored introduction generation."
    )
```

In the output compilation block, add after Section 1's output lines and before Section 2's:

```python
output_lines.append("=" * 60)
output_lines.append("SECTION 1.5 \u2013 INTRODUCE YOURSELF")
output_lines.append(f"({profile['label']} register)")
output_lines.append("-" * 60)
output_lines.append(section_intro)
output_lines.append("")
```

Remove the `""` placeholder for `section_intro` in the `generate_prep_docx()` call (from Task 2) — it is now a real value.

- [ ] **Step 5: Run test to confirm it passes**

```
pytest tests/phase5/test_interview_prep.py::test_intro_monologue_in_output -v
```
Expected: PASS

- [ ] **Step 6: Run all phase5 tests**

```
pytest tests/phase5/test_interview_prep.py -v -k "not live"
```
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "Add Section 1.5: Introduce Yourself with stage-tailored intro monologue"
```

---

## Task 10: Parameterize Section 2 (Story Bank) by stage

**Files:**
- Modify: `scripts/phase5_interview_prep.py`

- [ ] **Step 1: Write failing test**

Add to `tests/phase5/test_interview_prep.py`:

```python
def test_section2_story_count_in_api_payload():
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()

    with tempfile.TemporaryDirectory() as tmpdir:
        generate_prep(client, role_data, "recruiter",
                      str(Path(tmpdir) / "interview_prep_recruiter.txt"),
                      str(Path(tmpdir) / "interview_prep_recruiter.docx"))

    # Section 2 is call index 2 (S1=0, S1.5=1, S2=2)
    section2_call = str(client.messages.create.call_args_list[2])
    assert "1-2" in section2_call
    assert "headline" in section2_call.lower()
    assert "Do NOT reference gaps" in section2_call or "Suppress gap" in section2_call
```

- [ ] **Step 2: Run test to confirm it fails**

```
pytest tests/phase5/test_interview_prep.py::test_section2_story_count_in_api_payload -v
```
Expected: FAIL

- [ ] **Step 3: Add _build_section2_prompt() helper**

Add after `_build_intro_prompt()`:

```python
def _build_section2_prompt(jd, story_context, candidate_profile, profile):
    """Build the Section 2 story bank prompt, parameterized by stage profile."""
    _depth_instructions = {
        "headline": (
            "STORY DEPTH: Headline only.\n"
            "- Provide story headline + one-sentence result for each story\n"
            "- Do NOT expand to full STAR format\n"
            "- Omit 'If probed' branch"
        ),
        "full": (
            "STORY DEPTH: Full STAR with probe branch.\n"
            "- Full Situation / Task / Action / Result for each story\n"
            "- Include one 'If probed' branch per story (one additional sentence)"
        ),
        "full_technical": (
            "STORY DEPTH: Full STAR with technical specificity.\n"
            "- Full Situation / Task / Action / Result for each story\n"
            "- Use tool-specific language (name tools, models, frameworks used)\n"
            "- Include peer-credible detail a working engineer would recognize\n"
            "- Include one 'If probed' branch per story"
        ),
    }

    _gap_instructions = {
        "omit": "GAP FRAMING: Do NOT reference gaps or limitations in any story framing.",
        "note": (
            "GAP FRAMING: Where a story might brush against a known gap, "
            "include a brief one-sentence awareness note."
        ),
        "full": "GAP FRAMING: Integrate full gap awareness into story framing where relevant.",
        "full_peer": (
            "GAP FRAMING: Integrate full gap awareness into story framing where relevant, "
            "with peer-level directness."
        ),
    }

    role_fit_instruction = (
        "2 sentences only -- lead with strongest fit signal."
        if profile["story_depth"] == "headline"
        else "3-4 honest sentences -- genuine strengths and real gaps."
    )

    return (
        f"Generate employer-attributed interview stories for a {profile['label']}.\n\n"
        f"CANDIDATE PROFILE (PII removed):\n{candidate_profile[:2500]}\n\n"
        f"RESUME SUBMITTED FOR THIS ROLE -- with employer context:\n{story_context[:3000]}\n\n"
        f"JOB DESCRIPTION:\n{jd[:2000]}\n\n"
        f"CRITICAL INSTRUCTIONS:\n"
        f"- Every story MUST be grounded in the bullets shown above\n"
        f"- Every story MUST include employer attribution "
        f"(\"During my time at [Employer] as [Title], [dates]...\")\n"
        f"- Do NOT invent metrics or outcomes\n\n"
        f"{_depth_instructions[profile['story_depth']]}\n\n"
        f"{_gap_instructions[profile['gap_behavior']]}\n\n"
        f"Generate {profile['story_count']} stories. Use this format:\n\n"
        f"ROLE FIT ASSESSMENT:\n[{role_fit_instruction}]\n\n"
        f"KEY THEMES TO LEAD WITH:\n"
        f"Theme 1 -- [Name]: [1-2 sentences]\n"
        f"Theme 2 -- [Name]: [1-2 sentences]\n\n"
        f"STORY BANK:\n\n"
        f"STORY 1 -- [JD Requirement this addresses]:\n"
        f"Employer: [Company | Title | Dates]\n"
        f"Situation: [Context]\n"
        f"Task: [What needed to be done]\n"
        f"Action: [What YOU did -- first person]\n"
        f"Result: [Outcome -- qualitative acceptable]\n"
        f"If probed: [One additional sentence -- omit for headline depth]\n\n"
        f"[Continue for all stories in the {profile['story_count']} range]\n\n"
        f"LIKELY INTERVIEW QUESTIONS:\n"
        f"[5-8 questions likely to be asked, with one-line approach each]"
    )
```

- [ ] **Step 4: Replace the inline story_prompt in generate_prep()**

Find the `story_prompt = f"""..."""` block in `generate_prep()` and replace it with:

```python
story_prompt = _build_section2_prompt(jd, story_context, candidate_profile, profile)
```

- [ ] **Step 5: Run test to confirm it passes**

```
pytest tests/phase5/test_interview_prep.py::test_section2_story_count_in_api_payload -v
```
Expected: PASS

- [ ] **Step 6: Run all phase5 tests**

```
pytest tests/phase5/test_interview_prep.py -v -k "not live"
```
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "Parameterize Section 2 story bank prompt by stage; story count, depth, gap framing"
```

---

## Task 11: Section 3 — conditional gap logic and short tenure prepend

**Files:**
- Modify: `scripts/phase5_interview_prep.py`
- Modify: `tests/phase5/test_interview_prep.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/phase5/test_interview_prep.py`:

```python
def test_recruiter_skips_gap_api_call():
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep_recruiter.txt"
        generate_prep(client, role_data, "recruiter",
                      str(txt_path),
                      str(Path(tmpdir) / "interview_prep_recruiter.docx"))
        content = txt_path.read_text(encoding="utf-8")

    # S1=0, S1.5=1, S2=2, S3 skipped, S4=3 -- total 4 calls
    assert client.messages.create.call_count == 4, (
        f"Expected 4 API calls for recruiter, got {client.messages.create.call_count}"
    )
    assert "do not volunteer gaps" in content.lower()


def test_short_tenure_block_in_output():
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep_hiring_manager.txt"
        generate_prep(client, role_data, "hiring_manager",
                      str(txt_path),
                      str(Path(tmpdir) / "interview_prep_hiring_manager.docx"))
        content = txt_path.read_text(encoding="utf-8")

    # The fixture profile has a SHORT TENURE EXPLANATION section
    assert "SHORT TENURE EXPLANATION" in content
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/phase5/test_interview_prep.py::test_recruiter_skips_gap_api_call tests/phase5/test_interview_prep.py::test_short_tenure_block_in_output -v
```
Expected: both FAIL

- [ ] **Step 3: Add _build_gap_prompt() helper**

Add after `_build_section2_prompt()`:

```python
def _build_gap_prompt(jd, gaps_section, candidate_profile, profile):
    """Build the Section 3 gap prep prompt, parameterized by stage profile."""
    peer_frame_block = ""
    if profile["gap_behavior"] == "full_peer":
        peer_frame_block = f"\n\n{profile['peer_frame_prompt']}"

    gap_depth_note = ""
    if profile["gap_behavior"] == "note":
        gap_depth_note = (
            "\nFor hiring manager stage: for each gap, include a brief note on how "
            "the gap might surface in a program context and how to address it proactively."
        )

    return (
        f"You are doing a two-step gap analysis grounded strictly in the JD text and "
        f"candidate profile. Follow these steps exactly.\n\n"
        f"STEP 1 -- EXTRACT ALL JD REQUIREMENTS:\n"
        f"Read the FULL job description below -- including required qualifications, preferred "
        f"qualifications, responsibilities, and any other stated criteria. Extract two lists:\n"
        f"  REQUIRED: skills, experience, tools, or credentials explicitly marked as required\n"
        f"  PREFERRED: skills or experience explicitly marked as preferred, desired, or a plus\n\n"
        f"Do not infer requirements from job type, title, seniority, or industry norms.\n"
        f"Only use what the JD text directly states.\n\n"
        f"FULL JOB DESCRIPTION:\n{jd}\n\n"
        f"STEP 2 -- CROSS-REFERENCE AGAINST CANDIDATE PROFILE:\n"
        f"Compare your extracted lists against the candidate profile below. A gap is valid if:\n"
        f"  - HARD GAP: JD lists it as REQUIRED and it is absent from the candidate's experience\n"
        f"  - PREFERRED GAP: JD lists it as PREFERRED and absent -- flag as lower severity\n\n"
        f"Expect to find 3-5 gaps. If you find zero, re-examine preferred qualifications.\n\n"
        f"CANDIDATE CONFIRMED GAPS:\n{gaps_section[:1500]}\n\n"
        f"CANDIDATE FULL PROFILE:\n{candidate_profile[:2000]}\n"
        f"{gap_depth_note}\n\n"
        f"For each gap provide a direct, confident talking point -- not apologetic.\n\n"
        f"Format exactly as:\n\n"
        f"GAP 1 -- [Topic] [REQUIRED or PREFERRED]:\n"
        f"Gap: [What the JD states and why it is a gap]\n"
        f"Honest answer: [What to say -- confident, not apologetic]\n"
        f"Bridge: [Connection to actual experience]\n"
        f"Redirect: [Strength to pivot toward]\n\n"
        f"GAP 2 -- [Topic] [REQUIRED or PREFERRED]:\n"
        f"[same format]\n\n"
        f"GAP 3 -- [Topic] [REQUIRED or PREFERRED]:\n"
        f"[same format]\n\n"
        f"HARD QUESTIONS TO PREPARE FOR:\n"
        f"[5 questions that will probe these gaps, with one-sentence approach each]"
        f"{peer_frame_block}"
    )
```

- [ ] **Step 4: Replace Section 3 logic in generate_prep()**

Find the Section 3 block in `generate_prep()` and replace it entirely:

```python
# --------------------------------------------------
# SECTION 3 -- GAP PREPARATION
# --------------------------------------------------
print("Section 3: Gap Preparation...")

short_tenure_raw = extract_profile_section(raw_profile, "SHORT TENURE EXPLANATION")
short_tenure_block = ""
if short_tenure_raw:
    short_tenure_block = (
        "SHORT TENURE EXPLANATION:\n"
        + strip_pii(short_tenure_raw)
        + "\n\n" + "=" * 40 + "\n\n"
    )

if profile["gap_behavior"] == "omit":
    section3 = (
        short_tenure_block
        + "Gap prep omitted -- do not volunteer gaps in a recruiter screen."
    )
else:
    gap_prompt = _build_gap_prompt(jd, gaps_section, candidate_profile, profile)
    response3 = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": gap_prompt}]
    )
    section3 = short_tenure_block + response3.content[0].text
```

- [ ] **Step 5: Run tests to confirm both pass**

```
pytest tests/phase5/test_interview_prep.py::test_recruiter_skips_gap_api_call tests/phase5/test_interview_prep.py::test_short_tenure_block_in_output -v
```
Expected: both PASS

- [ ] **Step 6: Run all phase5 tests**

```
pytest tests/phase5/test_interview_prep.py -v -k "not live"
```
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "Section 3: skip API for recruiter, short tenure prepend, peer frame for team_panel"
```

---

## Task 12: Section 4 — stage-specific questions from profile

**Files:**
- Modify: `scripts/phase5_interview_prep.py`

- [ ] **Step 1: Replace Section 4 prompt in generate_prep()**

No new test needed — the existing `test_generate_prep_txt_has_required_sections` already checks for "QUESTION" in output. The key change is wiring `profile["questions_prompt"]` instead of the generic questions prompt.

Find the `questions_prompt = f"""..."""` block in `generate_prep()` and replace:

```python
questions_prompt = profile["questions_prompt"].format(
    jd=jd[:2000],
    profile_summary=strip_pii(candidate_profile[:800]),
)
```

- [ ] **Step 2: Run all phase5 tests**

```
pytest tests/phase5/test_interview_prep.py -v -k "not live"
```
Expected: all PASS

- [ ] **Step 3: Commit**

```bash
git add scripts/phase5_interview_prep.py
git commit -m "Wire Section 4 questions prompt from stage profile; stage-specific question sets"
```

---

## Task 13: Update generate_prep_docx() for new sections and peer frame

**Files:**
- Modify: `scripts/phase5_interview_prep.py`
- Modify: `tests/phase5/test_interview_prep.py`

- [ ] **Step 1: Write failing test**

Add to `tests/phase5/test_interview_prep.py`:

```python
def test_team_panel_peer_frame_bold_in_docx():
    from scripts.phase5_interview_prep import generate_prep

    # Provide mock response that contains a Peer Frame label
    mock_with_peer_frame = MOCK_PREP_RESPONSE + "\nPeer Frame: I understand this gap.\n"
    client = make_mock_client(mock_with_peer_frame)
    role_data = make_role_data()

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep_team_panel.txt"
        docx_path = Path(tmpdir) / "interview_prep_team_panel.docx"
        generate_prep(client, role_data, "team_panel", str(txt_path), str(docx_path))
        doc = Document(str(docx_path))

    # Find any paragraph containing "Peer Frame:" -- its first run should be bold
    peer_frame_paragraphs = [
        p for p in doc.paragraphs if p.text.startswith("Peer Frame:")
    ]
    assert peer_frame_paragraphs, "No 'Peer Frame:' paragraph found in docx"
    assert peer_frame_paragraphs[0].runs[0].bold, "Peer Frame label run should be bold"
```

- [ ] **Step 2: Run test to confirm it fails**

```
pytest tests/phase5/test_interview_prep.py::test_team_panel_peer_frame_bold_in_docx -v
```
Expected: FAIL

- [ ] **Step 3: Update generate_prep_docx() — add Peer Frame to bold label list**

Find the `parse_and_add_section` inner function's `elif re.match(...)` line for story labels and add `Peer Frame`:

```python
elif re.match(r'^(Situation|Task|Action|Result|Employer|'
              r'Gap|Honest answer|Bridge|Redirect|Peer Frame|'
              r'If probed|Theme \d|Follow-up):', stripped):
```

- [ ] **Step 4: Replace section rendering block in generate_prep_docx()**

Find and replace the entire section rendering block in `generate_prep_docx()` (the four `add_heading` / `parse_and_add_section` groups for S1–S4) with:

```python
# Section 1
add_heading("Company & Role Brief", level=1)
add_normal(f"({stage_profile['label']} -- verify currency before interview)")
parse_and_add_section(section1)

# Section 1.5
add_heading("Introduce Yourself", level=1)
add_normal(f"Tailored for {stage_profile['label']} register.")
parse_and_add_section(section_intro)

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
```

- [ ] **Step 5: Run test to confirm it passes**

```
pytest tests/phase5/test_interview_prep.py::test_team_panel_peer_frame_bold_in_docx -v
```
Expected: PASS

- [ ] **Step 6: Run all phase5 tests**

```
pytest tests/phase5/test_interview_prep.py -v -k "not live"
```
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "Docx: add Introduce Yourself section, Peer Frame bold label, stage header"
```

---

## Task 14: Update script header comment and version string

**Files:**
- Modify: `scripts/phase5_interview_prep.py` (top comment block and version strings)

- [ ] **Step 1: Update the script header comment**

Replace the top docstring in `phase5_interview_prep.py`:

```python
# ==============================================
# phase5_interview_prep.py
# Generates stage-aware interview preparation
# materials for a specific job application.
#
# Improvements over v2:
#   - --interview_stage parameter drives all
#     section content (recruiter / hiring_manager
#     / team_panel)
#   - "Introduce Yourself" section tailored per
#     stage from candidate_profile.md
#   - Short tenure explanation prepended to
#     gap prep section at all stages
#   - Stage-specific questions prompt per audience
#   - --dry_run flag for profile validation
#   - Stage-specific output filenames
#
# Outputs to data/job_packages/[role]/:
#   interview_prep_[stage].txt
#   interview_prep_[stage].docx
#
# Sections:
#   1:   Company & Role Brief (web-informed)
#   1.5: Introduce Yourself (stage-tailored)
#   2:   Story Bank (library-grounded)
#   3:   Gap Preparation (stage-conditional)
#   4:   Questions to Ask (stage-specific)
#
# Usage:
#   python scripts/phase5_interview_prep.py \
#     --role Viasat_SE_IS \
#     --interview_stage hiring_manager
#   python scripts/phase5_interview_prep.py \
#     --role Viasat_SE_IS --dry_run
# ==============================================
```

Also update the version string in `generate_prep()` output header:

```python
output_lines.append("INTERVIEW PREP PACKAGE v3")
```

And in `main()`:

```python
print("PHASE 5 \u2013 INTERVIEW PREP GENERATOR v3")
```

- [ ] **Step 2: Run syntax check**

```
python -m py_compile scripts/phase5_interview_prep.py && echo "OK"
```
Expected: `OK`

- [ ] **Step 3: Run full phase5 test suite one final time**

```
pytest tests/phase5/test_interview_prep.py -v -k "not live"
```
Expected: all PASS — confirm count matches (5 original + 9 new = 14 tests)

- [ ] **Step 4: Commit**

```bash
git add scripts/phase5_interview_prep.py
git commit -m "Update script header comment and version string to v3"
```

---

## Task 15: Final verification

- [ ] **Step 1: Run full project test suite**

```
pytest tests/ -v -k "not live"
```
Expected: all tests PASS with no regressions outside phase5

- [ ] **Step 2: Run syntax check on modified script**

```
python -m py_compile scripts/phase5_interview_prep.py && echo "Syntax OK"
```
Expected: `Syntax OK`

- [ ] **Step 3: Verify --help output reflects new arguments**

```
python scripts/phase5_interview_prep.py --help
```
Expected: shows `--interview_stage` with `{recruiter,hiring_manager,team_panel}` and `--dry_run`

- [ ] **Step 4: Final commit if any cleanup needed, otherwise done**

```bash
git status
```
Expected: clean working tree (all changes committed across Tasks 1-14)
```
