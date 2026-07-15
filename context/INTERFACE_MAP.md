# Interface Map

**Update triggers:** CLI arg added/removed/renamed · public/exported function
added/removed/renamed · file I/O path changed · new script added.
Renaming or restructuring an internal helper does NOT trigger an update.

Last verified: 2026-06-20

---

## Section 1 — Shared Modules

### scripts/config.py

**Import:** `from scripts.config import <name>`

**Constants:**

| Name | Value |
|------|-------|
| `JOBS_PACKAGES_DIR` | `"data/job_packages"` |
| `EXPERIENCE_LIBRARY_JSON` | `"data/experience_library/experience_library.json"` |
| `CANDIDATE_PROFILE_PATH` | `"data/experience_library/candidate_profile.md"` |
| `RESUME_TEMPLATE` | `"templates_local/resume_template.docx"` |
| `RESUMES_DIR` | `"resumes"` |
| `CONTACTS_TRACKER_PATH` | `"data/tracker/contact_pipeline.xlsx"` |
| `MODEL_SONNET` | `"claude-sonnet-4-6"` |
| `MODEL_HAIKU` | `"claude-haiku-4-5-20251001"` |

---

### scripts/utils/candidate_config.py

**Import:** `from scripts.utils import candidate_config`

```python
def load() -> dict
def get_hardcoded_rules(document_type: str = "resume") -> list[tuple[str, str, str, bool]]
def build_known_facts() -> str
```

| Function | Returns | Behavior / side effects / errors |
|----------|---------|----------------------------------|
| `load()` | `dict` | Loads `context/candidate/candidate_config.yaml`; result cached after first call; raises `FileNotFoundError` if absent |
| `get_hardcoded_rules(document_type="resume")` | `list[tuple]` | Returns `(rule_name, pattern, fix, case_sensitive)` tuples; universal em-dash rule hardcoded; remaining rules from `style_rules` in config |
| `build_known_facts()` | `str` | Builds a `CONFIRMED FACTS` text block for Claude prompts; combines scalar PII from `.env` with structured career data from `candidate_config.yaml`; covers name, location, phone, email, LinkedIn, GitHub, education, certifications, clearance, military service, confirmed skills, confirmed gaps, and style rules |

---

### scripts/utils/pii_filter.py

**Import:** `from scripts.utils.pii_filter import strip_pii`

```python
def strip_pii(text: str) -> str
def verify_strip(text: str) -> list[str]
```

| Function | Returns | Behavior / side effects / errors |
|----------|---------|----------------------------------|
| `strip_pii(text)` | `str` | Loads PII values from `.env`; replaces all occurrences in `text` before any API call; must wrap all prompt strings sent to Claude; handles name variants, phone format variants, URL prefix variants for LinkedIn/GitHub |
| `verify_strip(text)` | `list[str]` | Returns list of PII type labels (`name`, `phone`, `email`, `linkedin`, `github`) still detected in `text` after stripping; empty list means clean; use for testing and validation only |

---

### scripts/utils/library_parser.py

**Import:** `from scripts.utils.library_parser import parse_library, add_keywords, save_employers, save_summaries`

```python
def parse_library(filepath: str, track_line_numbers: bool = False) -> tuple[dict, list]
def add_keywords(employers: dict, summaries: list, client, keyword_delay: float = 0.5) -> None
def save_employers(employers: dict, output_dir: str) -> list[str]
def save_summaries(summaries: list, filepath: str) -> None
```

| Function | Returns | Behavior / side effects / errors |
|----------|---------|----------------------------------|
| `parse_library(filepath, track_line_numbers=False)` | `tuple[dict, list]` | Full parse of `experience_library.md` at `filepath`; returns `(employers_dict, summaries_list)`; when `track_line_numbers=True`, each bullet dict gains a 1-based `line_number` field; bullet IDs are assigned during parse |
| `add_keywords(employers, summaries, client, keyword_delay=0.5)` | `None` | Calls Claude API (`MODEL_SONNET`) to generate 5-8 keywords per bullet and summary; mutates `employers` and `summaries` in place; sleeps `keyword_delay` seconds between API calls; skips flagged bullets |
| `save_employers(employers, output_dir)` | `list[str]` | Writes one JSON file per employer under `output_dir` (created if absent); returns list of filenames saved; filename derived from employer name (lowercase, underscores, 40-char truncation) |
| `save_summaries(summaries, filepath)` | `None` | Writes `{"total": N, "summaries": [...]}` JSON to `filepath` with `indent=2`, non-ASCII preserved |

---

### scripts/utils/domain_config.py

**Import:** `from scripts.utils import domain_config`

```python
def load() -> dict
def get_label() -> str
```

| Function | Returns | Behavior / side effects / errors |
|----------|---------|----------------------------------|
| `load()` | `dict` | Loads `context/domain/domain_config.yaml`; result cached after first call; raises `FileNotFoundError` if absent |
| `get_label()` | `str` | Returns the `domain_label` string from `domain_config.yaml`; calls `load()` internally; raises `KeyError` if `domain_label` key is missing from config |

---

### scripts/interview_library_parser.py

**Import:** `from scripts.interview_library_parser import init_library, write_library, load_tags, get_stories, get_gap_responses, get_questions`

```python
def init_library() -> None
def write_library(library: dict) -> None
def load_tags() -> list[str]
def get_stories(tags: list[str] | None = None, role: str | None = None, stage: str | None = None) -> list[dict]
def get_gap_responses(tags: list[str] | None = None, role: str | None = None, gap_label: str | None = None) -> list[dict]
def get_questions(tags: list[str] | None = None, role: str | None = None, stage: str | None = None) -> list[dict]
```

| Function | Returns | Behavior / side effects / errors |
|----------|---------|----------------------------------|
| `init_library()` | `None` | Creates empty `data/interview_library.json` if absent; never overwrites existing content |
| `write_library(library)` | `None` | Writes `library` dict to `data/interview_library.json` with `indent=2`, non-ASCII preserved |
| `load_tags()` | `list[str]` | Returns controlled tag vocabulary from `templates/interview_library_tags.json`; empty list if file absent |
| `get_stories(tags=None, role=None, stage=None)` | `list[dict]` | AND-logic across filters; `tags` uses OR within the list; `stage` accepted for API compatibility but not applied (stories have no stage field); empty list on no match |
| `get_gap_responses(tags=None, role=None, gap_label=None)` | `list[dict]` | AND-logic across filters; `tags` uses OR within the list; `gap_label` is case-insensitive exact match on `gap_label` field; empty list on no match |
| `get_questions(tags=None, role=None, stage=None)` | `list[dict]` | AND-logic across filters; `tags` uses OR within the list; `stage` exact match on stage field (`recruiter` / `hiring_manager` / `team_panel`); empty list on no match |

---

### scripts/phase5_debrief_utils.py

**Import:** `from scripts.phase5_debrief_utils import load_debriefs, load_all_debriefs, get_story_performance_signal, get_gap_performance_signal, load_salary_actuals, build_continuity_section, find_unmatched_debrief_content, has_debrief_for_stage`

```python
def load_debriefs(role: str) -> list[dict]
def load_all_debriefs() -> list[dict]
def get_story_performance_signal(library_id: str, all_debriefs: list) -> str | None
def get_gap_performance_signal(gap_label: str, all_debriefs: list) -> str | None
def load_salary_actuals(debriefs: list) -> dict | None
def build_continuity_section(debriefs: list) -> str
def find_unmatched_debrief_content(debriefs: list) -> tuple[list, list]
def has_debrief_for_stage(debriefs: list, stage: str, panel_label=None) -> bool
```

| Function | Returns | Behavior / side effects / errors |
|----------|---------|----------------------------------|
| `load_debriefs(role)` | `list[dict]` | Loads all filed debrief JSON files from `data/debriefs/[role]/`; returns list of parsed dicts sorted by `metadata.interview_date`; empty list if directory absent or no filed debriefs; silently skips malformed JSON files |
| `load_all_debriefs()` | `list[dict]` | Loads debriefs across all role subdirectories under `data/debriefs/`; returns empty list if directory absent |
| `get_story_performance_signal(library_id, all_debriefs)` | `str \| None` | Scans `all_debriefs` for uses of `library_id`; returns summary string of landed counts (e.g. `"Used 3 times across roles: [yes x2 / no x1]"`); `None` if not found |
| `get_gap_performance_signal(gap_label, all_debriefs)` | `str \| None` | Scans `all_debriefs` for uses of `gap_label` (case-insensitive); returns summary string of `response_felt` counts; `None` if not found |
| `load_salary_actuals(debriefs)` | `dict \| None` | Scans `debriefs` in reverse order for the most recent salary exchange entry with a range; returns dict with keys `range_given_min`, `range_given_max`, `candidate_anchor`, `candidate_floor`, `notes`, `interview_date`, `stage`; `None` if no salary data found |
| `build_continuity_section(debriefs)` | `str` | Builds a formatted `CONTINUITY SUMMARY` text block from all debriefs; covers interviewers, advancement read, stories used (with landed outcome), gaps surfaced, and `what_i_said`; returns empty string if `debriefs` is empty |
| `find_unmatched_debrief_content(debriefs)` | `tuple[list, list]` | Compares debrief `library_id` refs and gap labels against the current `interview_library.json`; returns `(unmatched_stories, unmatched_gaps)` lists for entries in debriefs that have no library record |
| `has_debrief_for_stage(debriefs, stage, panel_label=None)` | `bool` | Returns `True` if any debrief matches `stage` (and optionally `panel_label`); `False` otherwise |

---

## Section 2 — Production Scripts

### scripts/init_candidate.py

**Invoke:** `python -m scripts.init_candidate`

**Args:** *(none)*

**File I/O:**

| Reads | Writes |
|-------|--------|
| `context/candidate/candidate_config.example.yaml` | `context/candidate/candidate_config.yaml` |

---

### scripts/init_job_package.py

**Invoke:** `python -m scripts.init_job_package --role <role> --req <req>`

**Args:**

| Arg | Type | Required | Default | Notes |
|-----|------|----------|---------|-------|
| `--role` | str | Required | — | Job package folder name; underscores only, no special characters |
| `--req` | str | Required | — | Requisition number; must be unique among active rows in `data/jobs.csv` |

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/jobs.csv` | `data/jobs.csv` (appends one row) |
| | `data/job_packages/[role]/job_description.txt` (creates empty file) |

---

### scripts/pipeline_report.py

**Invoke:** `python -m scripts.pipeline_report`

**Args:** *(none)*

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/tracker/job_pipeline.xlsx` | `outputs/pipeline_report_YYYYMMDD_HHMM.txt` |
| `data/jobs.csv` | |

---

### scripts/phase2_job_ranking.py

**Invoke:** `python -m scripts.phase2_job_ranking`

**Args:** *(none)*

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/jobs.csv` | `outputs/ranked_jobs.csv` |
| `data/job_packages/[role]/job_description.txt` | `outputs/ranking_report_YYYYMMDD_HHMM.txt` |

---

### scripts/phase2_semantic_analyzer.py

**Invoke:** `python -m scripts.phase2_semantic_analyzer`

**Args:** *(none)*

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/jobs.csv` | `outputs/semantic_analysis_YYYYMMDD_HHMM.txt` |
| `data/job_packages/[role]/job_description.txt` | |
| `data/experience_library/candidate_profile.md` | |
| `outputs/ranked_jobs.csv` (optional) | |

---

### scripts/phase3_parse_library.py

**Invoke:** `python -m scripts.phase3_parse_library`

**Args:** *(none)*

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/experience_library/experience_library.md` | `data/experience_library/employers/[employer_slug].json` |
| | `data/experience_library/summaries.json` |

---

### scripts/phase3_parse_employer.py

**Invoke:** `python -m scripts.phase3_parse_employer "Employer Name" [--keywords]`

**Args:**

| Arg | Type | Required | Default | Notes |
|-----|------|----------|---------|-------|
| `employer` | str | Required | — | Positional; case-insensitive substring match against `## Employer Name` headings in `experience_library.md`; errors if zero or multiple matches |
| `--keywords` | flag | Optional | False | Generate Claude keywords for matched employer bullets via API |

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/experience_library/experience_library.md` | `data/experience_library/employers/[employer_slug].json` |

---

### scripts/phase3_compile_library.py

**Invoke:** `python -m scripts.phase3_compile_library`

**Args:** *(none)*

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/experience_library/employers/*.json` | `data/experience_library/experience_library.json` |
| `data/experience_library/summaries.json` | |

---

### scripts/phase3_build_candidate_profile.py

**Invoke:** `python -m scripts.phase3_build_candidate_profile`

**Args:** *(none)*

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/experience_library/experience_library.json` | `data/experience_library/candidate_profile.md` |
| `data/experience_library/summaries.json` (fallback if not embedded in library JSON) | |

---

### scripts/phase4_resume_generator.py

**Invoke:** `python -m scripts.phase4_resume_generator --stage {1|3|4} --role ROLE`

**Args:**

| Arg | Type | Required | Default | Notes |
|-----|------|----------|---------|-------|
| `--stage` | int | Required | — | 1, 3, or 4; stage 2 is manual (no script) |
| `--role` | str | Required | — | Job package folder name under `data/job_packages/` |

**File I/O:**

| Stage | Reads | Writes |
|-------|-------|--------|
| 1 | `data/job_packages/[role]/job_description.txt`, `data/experience_library/experience_library.json`, `data/experience_library/candidate_profile.md` | `data/job_packages/[role]/stage1_draft.txt` |
| 3 | `data/job_packages/[role]/stage2_approved.txt`, `data/job_packages/[role]/job_description.txt` | `data/job_packages/[role]/stage3_review.txt` |
| 4 | `data/job_packages/[role]/stage4_final.txt` (preferred) or `data/job_packages/[role]/stage2_approved.txt` (fallback), `templates_local/resume_template.docx` | `resumes/[role]/[role]_Resume.docx` |

**Notes:** Stage 4 automatically invokes `check_resume.py` as a subprocess after docx generation.

---

### scripts/phase4_interactive.py

**Invoke:** `python -m scripts.phase4_interactive`

**Args:** *(none — interactive TUI; role selected from numbered menu at runtime)*

**File I/O:**

| Stage | Reads | Writes |
|-------|-------|--------|
| 1 | `data/experience_library/experience_library.json`, `data/job_packages/[role]/job_description.txt`, `data/experience_library/candidate_profile.md` | `data/job_packages/[role]/stage1_draft.txt` |
| 3 | `data/job_packages/[role]/stage2_approved.txt`, `data/job_packages/[role]/job_description.txt` | `data/job_packages/[role]/stage3_review.txt` |
| 4 | `data/job_packages/[role]/stage2_approved.txt` (copied to stage4_final.txt), `templates_local/resume_template.docx` | `data/job_packages/[role]/stage4_final.txt`, `resumes/[role]/[role]_Resume.docx` |

**Notes:** Wraps `phase4_resume_generator.py` stage functions. Opens output files with the system default application after each stage. Stage 2 is an in-editor review loop: after user saves stage1_draft.txt, the script copies it to stage2_approved.txt. Stage 3 is a re-runnable loop until the user accepts. Stage 4 copies stage2_approved.txt to stage4_final.txt before docx generation.

---

### scripts/phase4_backport.py

**Invoke:** `python -m scripts.phase4_backport --role ROLE [--dry-run] [--net-new-threshold FLOAT] [--variant-floor FLOAT]`

**Args:**

| Arg | Type | Required | Default | Notes |
|-----|------|----------|---------|-------|
| `--role` | str | Required | — | Job package folder name under `data/job_packages/` |
| `--dry-run` | flag | Optional | False | Print findings without writing any files |
| `--net-new-threshold` | float | Optional | 85.0 | Fuzzy match score at or above which a bullet is classified as already present in the library |
| `--variant-floor` | float | Optional | 60.0 | Fuzzy match floor; scores in `[variant-floor, net-new-threshold)` are classified as variant |

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/job_packages/[role]/stage4_final.txt` (preferred) or `data/job_packages/[role]/stage2_approved.txt` (fallback) | `data/job_packages/[role]/backport_staged.md` (skipped if `--dry-run`) |
| `data/experience_library/experience_library.md` | `data/backport_registry.json` (skipped if `--dry-run`) |
| `data/backport_registry.json` (if exists) | |

**Notes:** Uses `rapidfuzz.fuzz.token_sort_ratio` for bullet similarity scoring. Delegates library parsing to `scripts/utils/library_parser.py` with `track_line_numbers=True`. Registry is appended (not overwritten) on each run; warns but does not block re-runs for the same role.

---

### scripts/phase4_cover_letter.py

**Invoke:** `python -m scripts.phase4_cover_letter --stage {1|4} --role ROLE`

**Args:**

| Arg | Type | Required | Default | Notes |
|-----|------|----------|---------|-------|
| `--stage` | int | Required | — | 1 (generate draft) or 4 (build docx); stages 2 and 3 are manual / `check_cover_letter.py` |
| `--role` | str | Required | — | Job package folder name under `data/job_packages/` |

**File I/O:**

| Stage | Reads | Writes |
|-------|-------|--------|
| 1 | `data/job_packages/[role]/job_description.txt`, `context/candidate/CANDIDATE_BACKGROUND.md`, `data/job_packages/[role]/stage4_final.txt` or `stage2_approved.txt` (optional resume bullets), `data/job_packages/[role]/stage3_review.txt` (optional coverage gaps) | `data/job_packages/[role]/cl_stage1_draft.txt` |
| 4 | `data/job_packages/[role]/cl_stage4_final.txt`, `templates_local/resume_template.docx` | `resumes/[role]/[role]_CoverLetter.docx` |

**Notes:** Stage 1 makes three API calls: hiring manager extraction, traditional letter generation, and application paragraph generation. Resume bullet source (`stage4_final.txt` preferred, `stage2_approved.txt` fallback) is optional — if neither exists, generation proceeds using background only. Coverage gaps from `stage3_review.txt` (resume review file) are passed as negative constraints to both generation calls.

---

### scripts/check_resume.py

**Invoke:** `python -m scripts.check_resume --role ROLE`

**Args:**

| Arg | Type | Required | Default | Notes |
|-----|------|----------|---------|-------|
| `--role` | str | Required | — | Job package folder name under `data/job_packages/` |

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/job_packages/[role]/stage2_approved.txt` | `data/job_packages/[role]/check_results.txt` |
| `context/candidate/CANDIDATE_BACKGROUND.md` | |

**Notes:** Two-layer checker. Layer 1: fast string matching against hardcoded rules (from `candidate_config.get_hardcoded_rules`) and dynamic gap terms extracted from `CANDIDATE_BACKGROUND.md`. Layer 2: single API call for nuanced claims assessment. Lines inside sections listed in `PROJECT_SECTION_HEADERS` (currently `## INDEPENDENT PROJECT`) are exempt from Layer 1 gap-term matching and excluded from Layer 2 gap flagging via a prompt clarification — these are personal-project entries, not employment; hardcoded rules (em dash, banned language) still apply to them. All output is captured to `check_results.txt`; exit code is 1 if `Status: FAIL` appears in output, 0 otherwise. Also invoked automatically by `phase4_resume_generator.py --stage 4` as a subprocess.

---

### scripts/check_cover_letter.py

**Invoke:** `python -m scripts.check_cover_letter --role ROLE`

**Args:**

| Arg | Type | Required | Default | Notes |
|-----|------|----------|---------|-------|
| `--role` | str | Required | — | Job package folder name under `data/job_packages/` |

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/job_packages/[role]/cl_stage2_approved.txt` | `data/job_packages/[role]/cl_stage3_review.txt` |
| `context/candidate/CANDIDATE_BACKGROUND.md` | |

**Notes:** Mirrors `check_resume.py` architecture. Layer 2 emphasis is on implied gap fulfillment — cover letter prose can imply gap experience without naming gap terms directly. Also checks for banned generic opener phrases. Exit code is 1 if `Status: FAIL` appears in output, 0 otherwise.

---

### scripts/phase5_interview_prep.py

**Invoke:** `python -m scripts.phase5_interview_prep --role ROLE [--interview_stage STAGE] [--dry_run]`

**Args:**

| Arg | Type | Required | Default | Notes |
|-----|------|----------|---------|-------|
| `--role` | str | Required | — | Job package folder name under `data/job_packages/` |
| `--interview_stage` | str | Optional | — | One of: `recruiter` · `hiring_manager` · `team_panel` · `behavioral` · `technical_panel`; interactive menu shown if omitted |
| `--dry_run` | flag | Optional | — | Print stage profile and exit; no API calls or file writes |

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/job_packages/[role]/job_description.txt` | `data/job_packages/[role]/interview_prep_[stage].txt` |
| `data/experience_library/experience_library.json` | `data/job_packages/[role]/interview_prep_[stage].docx` |
| `data/experience_library/candidate_profile.md` | |
| `data/job_packages/[role]/stage4_final.txt` (preferred) or `data/job_packages/[role]/stage2_approved.txt` (fallback, optional) | |
| `data/interview_library.json` (via `interview_library_parser`) | |
| `templates/interview_library_tags.json` (via `interview_library_parser`) | |
| `data/debriefs/[role]/debrief_*_filed-*.json` (via `phase5_debrief_utils`, optional) | |

**Notes:** Generates a 5-section interview prep package (Company Brief, Introduce Yourself, Story Bank, Gap Prep, Questions to Ask). Stage profile controls story depth, gap behavior, salary inclusion, and question audience. Sections 1 uses the `web_search` tool. Library seeds (stories, gap responses, questions) are injected from `interview_library.json` based on JD tag matching. Debrief history injects performance signals into seeds and a Continuity Summary section if prior debriefs exist.

---

### scripts/phase5_workshop_capture.py

**Invoke:** `python -m scripts.phase5_workshop_capture --role ROLE --stage STAGE`

**Args:**

| Arg | Type | Required | Default | Notes |
|-----|------|----------|---------|-------|
| `--role` | str | Required | — | Job package folder name under `data/job_packages/` |
| `--stage` | str | Required | — | Interview stage matching the prep .docx filename (e.g. `hiring_manager`) |

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/job_packages/[role]/interview_prep_[stage].docx` | `data/interview_library.json` (appends / updates entries) |
| `templates/interview_library_tags.json` (via `interview_library_parser`) | |

**Notes:** Interactive TUI. Parses Story Bank, Gap Prep, and Questions to Ask sections from a workshopped prep .docx. For each parsed entry: auto-suggests tags from controlled vocabulary, prompts user to accept or override, then handles duplicates (skip / overwrite / rename). Italic paragraphs (coaching notes) are skipped during parse. Writes to library only on user confirmation.

---

### scripts/phase5_debrief.py

**Invoke:** `python -m scripts.phase5_debrief --role ROLE --stage STAGE [--init | --convert | --interactive]`

**Args:**

| Arg | Type | Required | Default | Notes |
|-----|------|----------|---------|-------|
| `--role` | str | Required | — | Job package folder name |
| `--stage` | str | Required | — | `recruiter_screen` · `hiring_manager` · `panel` · `final` |
| `--init` | flag | Optional | — | Mutually exclusive with `--convert`, `--interactive` |
| `--convert` | flag | Optional | — | Mutually exclusive with `--init`, `--interactive` |
| `--interactive` | flag | Optional | — | Mutually exclusive with `--init`, `--convert` |
| `--panel_label` | str | Optional | — | Required when stage is `panel` |

**File I/O:**

| Mode | Reads | Writes |
|------|-------|--------|
| `--init` | `templates/interview_debrief_template.yaml` | `data/debriefs/[role]/debrief_[stage]_draft.yaml` |
| `--convert` | `data/debriefs/[role]/debrief_[stage]_draft.yaml` | `data/debriefs/[role]/debrief_[stage]_[interview-date]_filed-[produced-date].json` |
| `--interactive` | *(none)* | `data/debriefs/[role]/debrief_[stage]_[interview-date]_filed-[produced-date].json` |

---

### scripts/phase5_thankyou.py

**Invoke:** `python -m scripts.phase5_thankyou --role ROLE --stage STAGE [--panel_label LABEL]`

**Args:**

| Arg | Type | Required | Default | Notes |
|-----|------|----------|---------|-------|
| `--role` | str | Required | — | Job package folder name under `data/job_packages/` |
| `--stage` | str | Required | — | Interview stage matching the debrief filename (e.g. `hiring_manager`) |
| `--panel_label` | str | Optional | — | Panel label used in debrief filename (e.g. `se_team`); required when debrief was filed with a panel label |

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/debriefs/[role]/debrief_[stage]_[*]_filed-*.json` (most recent match) | `data/job_packages/[role]/thankyou_[stage]_[lastname]_[date].txt` (one per interviewer) |
| `data/job_packages/[role]/job_description.txt` | `data/job_packages/[role]/thankyou_[stage]_[lastname]_[date].docx` (one per interviewer) |
| `data/job_packages/[role]/stage4_final.txt` (preferred) or `data/job_packages/[role]/stage2_approved.txt` (fallback, optional) | |
| `data/experience_library/candidate_profile.md` | |

**Notes:** Generates one `.txt` and one `.docx` per interviewer listed in the debrief. Tone is calibrated by interviewer title (executive / technical / recruiter / default). Interviewer notes from the debrief are the primary personalization anchor. Overwrite protection prompts per file. Output filenames include `panel_label` when provided.

---

### scripts/phase6_networking.py

**Invoke:** `python -m scripts.phase6_networking (--contact NAME | --list) [--stage {1|2|3|4}] [--inbound] [--role ROLE]`

**Args:**

| Arg | Type | Required | Default | Notes |
|-----|------|----------|---------|-------|
| `--contact` | str | Required* | — | Contact name (case-insensitive partial match); mutually exclusive with `--list` |
| `--list` | flag | Required* | — | Print all contacts sorted by stage; mutually exclusive with `--contact`; requires no other args |
| `--stage` | int | Optional | — | Message stage: 1 (connection request), 2 (referral ask), 3 (follow-up), 4 (close loop); mutually exclusive with `--inbound`; required when using `--contact` without `--inbound` |
| `--inbound` | flag | Optional | — | Generate a reply to an inbound LinkedIn connection request; mutually exclusive with `--stage` |
| `--role` | str | Optional | — | Job package folder name; required at Stage 2 to load `job_description.txt` |

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/tracker/contact_pipeline.xlsx` | `data/tracker/contact_pipeline.xlsx` (stage and status fields, on user confirm) |
| `data/job_packages/[role]/job_description.txt` (Stage 2 only) | |

**Notes:** Message output is printed to terminal only — no file written. On user confirm ("Did you send this?"), writes stage/status/date fields back to `contact_pipeline.xlsx`. `--list` exits after printing the contact table without making any API call or file write. Stage 2 requires `--role`; all other stages do not.

---

### scripts/utils/build_docs.py

**Invoke:** `python scripts/utils/build_docs.py [--all | --doc FILENAME]`

**Args:**

| Arg | Type | Required | Default | Notes |
|-----|------|----------|---------|-------|
| `--all` | flag | Optional | — | Assemble all known documents (default behavior when no flag given) |
| `--doc` | str | Optional | — | Assemble a single document by template filename (e.g. `README.md`); known targets: `README.md`, `USAGE.md`, `PROJECT_CONTEXT.md` |

**File I/O:**

| Reads | Writes |
|-------|--------|
| `docs/templates/[template_name]` | `README.md` |
| `docs/fragments/[fragment_name].md` (as referenced by `{{include: fragment_name}}` markers) | `USAGE.md` |
| | `context/PROJECT_CONTEXT.md` |

**Notes:** Replaces `{{include: name}}` markers in templates with the content of matching fragment files. Exits with code 1 if any fragment file is missing. Output files are prefixed with an assembled-by comment. Run after editing any file under `docs/templates/` or `docs/fragments/`.

---

### scripts/utils/find_duplicate_bullets.py

**Invoke:** `python -m scripts.utils.find_duplicate_bullets [--threshold FLOAT] [--library PATH]`

**Args:**

| Arg | Type | Required | Default | Notes |
|-----|------|----------|---------|-------|
| `--threshold` | float | Optional | 85.0 | Minimum `token_sort_ratio` score (0-100) to flag two bullets as duplicates |
| `--library` | str | Optional | `data/experience_library/experience_library.json` | Path to experience library JSON |

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/experience_library/experience_library.json` (default) | `outputs/duplicate_bullet_report_YYYYMMDD_HHMM.txt` |

**Notes:** Uses `rapidfuzz.fuzz.token_sort_ratio` for pairwise bullet similarity. Clusters overlapping pairs via union-find. Prompts for overwrite if output file already exists. Exits without writing if user declines overwrite.

---

### scripts/utils/normalize_library.py

**Invoke:** `python scripts/utils/normalize_library.py`

**Args:** *(none — all paths hardcoded)*

**File I/O:**

| Reads | Writes |
|-------|--------|
| `data/experience_library/experience_library.md` | `data/experience_library/experience_library_normalized.md` |

**Notes:** One-time cleanup utility. Merges tranche-suffixed employer sections (e.g. `## MERIDIAN AUTONOMY -- Tranche 4 Additions`) into single canonical employer sections. Also merges all `PROFESSIONAL SUMMARIES` sections and strips non-bullet structural sections (`FLAGS SUMMARY`, `MASTER FLAGS`, etc.). Does not overwrite the source file — the user must manually replace `experience_library.md` with the normalized output after review.

---

### utils/diagnose_*.py

Development diagnostics only — not part of the production workflow. No CLI spec documented.
