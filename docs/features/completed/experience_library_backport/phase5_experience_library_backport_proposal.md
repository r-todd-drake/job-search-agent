# Experience Library Backport

## User Story and Acceptance Criteria

### User Story
"As a job search system user, I want validated resume bullets from successful tailoring sessions automatically identified and staged for backport into the experience library, so that the library improves over time from market-tested outputs rather than only from raw source resumes."

### Background
The phase 3 pipeline runs one direction: `experience_library.md` → employer JSONs → `experience_library.json` → `candidate_profile.md`. Bullets refined or created during tailoring sessions (phase 4) have no path back into the library. When phase 3 scripts are re-run, any bullets added directly to the JSON are overwritten. The three validated resumes that prompted this feature (Viasat_SE_IS, BAH_LCI_MBSE, Anduril_Veh_Sys_Lead -- all resulting in recruiter or hiring manager callbacks) left zero net-new bullets in the library after the Apr 18 phase 3 run. The backport script recovers this class of loss going forward.

The source of truth is `experience_library.md`. All backport additions must land there first. The phase 3 scripts then propagate changes downstream.

The backport script reads `stage4_final.txt` as its primary input -- the fully workshopped stage file saved after the user acts on stage 3 semantic review findings. If `stage4_final.txt` is not present (e.g. after a heavy-rewrite pass where the user re-ran stage 3 without saving a stage 4), the script falls back to `stage2_approved.txt`. The `.docx` produced by stage 4 is presentation-only and is not a valid input. Source attribution for any net-new bullet is always `{role}_Resume` -- the script knows the resume it is processing.

---

### Acceptance Criteria

#### AC-1: Input Parsing
- Script resolves input from `data/job_packages/{role}/` where `{role}` is the value passed to `--role`
- Script looks for `stage4_final.txt` first; falls back to `stage2_approved.txt` if stage 4 is not found; errors with a clear message if neither exists
- Script reports which file was used at runtime
- Script correctly parses employer sections and bullet text from the stage file format
- Script reads `[Theme: ...]` tags as hints for suggested theme in staged output only -- tags are not used for source attribution
- Script handles missing or stale theme tags without erroring -- uses "UNKNOWN -- assign before committing" as the fallback theme

#### AC-2: Net-New Bullet Detection
- For each bullet in the input file, script checks whether the bullet text exists in `experience_library.md` using fuzzy match (not exact string match -- minor wording differences should not produce false negatives)
- Fuzzy match threshold is configurable; default is 85% similarity
- A bullet is classified as **net-new** if no match is found at or above the threshold
- A bullet is classified as **present** if a match is found -- script records the matched line number and theme for reference but takes no action
- A bullet is classified as **variant** if a partial match is found between threshold floor (configurable, default 60%) and the net-new threshold -- flagged for human review, not auto-staged

#### AC-3: Source Attribution Check
- For each bullet classified as **present**, script checks whether `{role}_Resume` appears in the `*Used in:*` tag of the matched library entry
- If absent, script flags it as a **source gap** -- bullet is in the library but this resume is not credited
- Source gap updates are staged separately from net-new additions in `backport_staged.md` (lower risk, simpler edit)

#### AC-4: Staged Output Generation
- Script produces a single output file: `backport_staged.md`
- Output file contains one entry per net-new bullet, formatted for direct paste into `experience_library.md`
- Each entry includes:
  - Employer name (from the input file section header)
  - Suggested theme (from the `[Theme: ...]` tag, or "UNKNOWN -- assign before committing" if absent)
  - Bullet text
  - `*Used in:*` tag: `{role}_Resume`
  - `*NOTE:*` placeholder: `[BACKPORT -- review before reuse. Outcome: {outcome_placeholder}]` where outcome is one of: recruiter callback, HM interview, panel, offer, no outcome
  - Outcome placeholder is a fill-in field; user records "recruiter callback," "HM interview," "panel," "offer," or "no outcome"
- Source gap entries are listed in a separate section of `backport_staged.md` with the matched line number and the missing source filename

#### AC-5: Employer Section Matching
- Script correctly maps each employer section in the input file to the corresponding employer section in `experience_library.md`
- Employer matching uses the employer name from the input file section header
- If no match is found, script flags the section as unrecognized and skips it with a warning -- does not error out

#### AC-6: Dry Run Mode
- Script supports a `--dry-run` flag that prints findings to console without writing `backport_staged.md`
- Dry run output includes: total bullets parsed, net-new count, variant count, present count, source gap count

#### AC-7: Validated Resume Registry
- Script maintains a simple registry file (`backport_registry.json`) recording which roles have been processed
- On subsequent runs, script warns if a role has already been processed -- prevents duplicate staging
- Registry records: role name, date processed, net-new count, source gap count, outcome (fill-in field, defaults to "pending")

---

### Out of Scope

- **Automatic write-back to `experience_library.md`:** Script stages content for human review; it does not modify the library directly. A human pastes from `backport_staged.md` into the correct location in the `.md`. This is intentional -- the `.md` is the source of truth and requires human judgment on placement, theme assignment, and NOTE content.
- **Phase 3 script execution:** Backport script does not trigger phase 3 re-runs. User runs phase 3 separately after updating the `.md`.
- **Keyword extraction for JSON entries:** Script produces `.md`-formatted output only. JSON keyword arrays, IDs, and priority flags are assigned during the phase 3 compile step, not here.
- **Comparison against employer JSONs directly:** Script reads `experience_library.md` only, not the compiled JSON or individual employer JSONs. The `.md` is the canonical source.
- **Stage 1 draft processing:** `stage1_draft.txt` is not a valid input. Stage 1 is raw generator output that has not been reviewed or workshopped by the user.
- **.docx processing:** The `.docx` generated by the stage 4 script is presentation-only and is not a valid input. Use `stage4_final.txt` instead.
- **Cover letter or interview prep backport:** Bullets appearing in cover letters or interview prep outputs are not in scope. Resume stage files only.
- **Automated outcome tracking integration:** The outcome field in `backport_registry.json` is a manual fill-in. Integration with an ATS or application tracker is a separate feature.

---

## Review Annotations
*This section is populated during the Chat spec review step (README process step 4). Do not fill in manually.*

Open items use `> ⚠ REVIEW:` and must be resolved before build starts.
Resolved items use `> ✅ RESOLVED:` and document what was decided.

---

> ✅ RESOLVED: **AC-2 fuzzy match library.** Use `rapidfuzz`. CC should install it as a project dependency (`pip install rapidfuzz`). Default thresholds remain 85% (net-new) and 60% (variant floor) as specified.

> ✅ RESOLVED: **Stage 1 draft filename as the source identifier.** Script appends `_Resume` suffix to the role name if not already present, producing e.g. `Viasat_SE_IS_Resume` to match the dominant library convention. This normalization is applied consistently to both the `*Used in:*` tag written to `backport_staged.md` and to source gap detection in AC-3.

> ✅ RESOLVED: **Invocation pattern.** Script uses `argparse` matching the phase 4 pattern. Invocation: `python scripts/phase4_backport.py --role Viasat_SE_IS`. The `--role` argument resolves the package directory as `data/job_packages/{role}/`; script finds `stage4_final.txt` or falls back to `stage2_approved.txt`. `--dry-run` flag is a boolean flag with no argument, matching `phase3_parse_employer.py --keywords` pattern. No `--stage` argument needed -- this script has one function.
