# Phase 5 Interview Prep -- Docx Formatting Upgrade

**Goal:** Rewrite `generate_prep_docx()` in `scripts/phase5_interview_prep.py` to produce
richly formatted Word documents matching the design system defined in the interview-prep
skill. The content pipeline (Claude API calls, library seeding, debrief integration) is
already complete and must not be touched. Only the docx rendering function changes.

---

## Before writing any code

Read these files in order:

1. `CLAUDE.md` -- safety rules, code style (en dashes, PII filter)
2. `scripts/phase5_interview_prep.py` -- read `generate_prep_docx()` in full to understand
   the current implementation before replacing it
3. `.claude/skills/interview-prep/references/design-tokens.md` -- the design system spec;
   all colors, typography, spacing, and layout component definitions (written in JS --
   you will translate these to python-docx equivalents)
4. `.claude/skills/interview-prep/references/stage-matrix.md` -- which sections are
   required vs. conditional per stage

Do not read the JS skill itself (`.claude/skills/interview-prep/SKILL.md`) for
implementation guidance -- the design-tokens.md and stage-matrix.md references are
the authoritative spec. The skill generates JS; you are generating Python.

---

## What to implement

### 1. Python equivalents of the design-token helpers

Translate the JS helpers from `design-tokens.md` into python-docx functions. Implement
each as a standalone helper at module level (not inside `generate_prep_docx`). Name them
to match the JS originals for traceability:

| JS helper | Python signature |
|---|---|
| `h1(text)` | `_h1(doc, text)` |
| `h2(text)` | `_h2(doc, text)` |
| `h3(text)` | `_h3(doc, text)` |
| `label(text)` | `_label(doc, text)` |
| `body(text, bold, italic)` | `_body(doc, text, bold=False, italic=False)` |
| `bullet(text)` | `_bullet(doc, text)` |
| `rule()` | `_rule(doc)` |
| `tintBox(paragraphs)` | `_tint_box(doc, lines)` -- shaded single-cell table |
| `alertBox(paragraphs)` | `_alert_box(doc, lines)` -- navy left-border table |
| `twoCol(left, right)` | `_two_col(doc, left_lines, right_lines)` -- borderless two-cell table |
| `storyBlock(...)` | `_story_block(doc, title, tag, situation, task, action, result, if_probed)` |
| `routingTable(rows)` | `_routing_table(doc, rows)` -- three-column, navy header, alternating rows |

Color constants (translate hex strings directly -- python-docx uses `RGBColor` or hex
strings depending on context):

```python
ACCENT       = "1F3A6B"   # dark navy
ACCENT_LIGHT = "E8EDF5"   # light blue-grey
RULE_COLOR   = "C0C8D8"
TEXT_PRIMARY   = "2C2C2C"
TEXT_SECONDARY = "3D3D3D"
TEXT_MUTED     = "6B7280"
TEXT_WHITE     = "FFFFFF"
ROW_ALT        = "F5F7FA"
```

Font: Aptos for all runs. Size scale matches design-tokens.md (sizes are in half-points
in docx convention -- e.g. 20 half-points = 10pt, 28 half-points = 14pt).

Page setup: US Letter, margins top/bottom 0.75in, left/right 0.875in.

### 2. Rewrite `generate_prep_docx()`

Replace the current implementation with one that uses the helpers above. The function
signature does not change -- same parameters in, same output (.docx file at
`output_path`). The sections to render and their order:

1. **Cover block** -- role, stage, date, resume source (label + value pairs)
2. **Section 1: Company & Role Brief** -- h1 heading, body text from `section1`
3. **Section 1.5: Introduce Yourself** -- h1 heading, intro monologue in a tint box
4. **Section 2: Story Bank** -- h1 heading, content from `section2`; parse STAR stories
   and render each with `_story_block()`; render the routing table if present
5. **Section 3: Gap Preparation** -- h1 heading, content from `section3`; render each
   gap's honest/bridge/redirect triad with labeled structure
6. **Section 4: Questions to Ask** -- h1 heading, each question in a tint box with
   rationale below
7. **Continuity Summary** (conditional -- only when `continuity_section` is non-empty) --
   h1 heading, body text; use alert box for the header note
   "(Reference record from prior interviews -- not prep guidance)"

Use `_rule()` between major sections (1, 1.5, 2, 3, 4, continuity). Not between
sub-sections within a section.

### 3. Content parsing

The section strings (section1, section2, section3, section4) come from Claude API
responses as plain text with structured markers. The existing `parse_and_add_section()`
helper already does basic line-by-line rendering -- examine it before replacing it.

For the upgrade, detect these patterns and render appropriately:

- Lines matching `^STORY \d+ --` or `^STAR Story` -- start of a story block; collect
  SITUATION/TASK/ACTION/RESULT/IF PROBED lines and pass to `_story_block()`
- Lines matching `^GAP \d+ --` -- start of a gap block; collect sub-lines with
  `_label()` + `_body()` pairs
- Lines matching `^#+\s` or ALL-CAPS followed by `:` -- render as h2 or label
- Lines starting with `-` or `•` -- render as `_bullet()`
- All other non-empty lines -- render as `_body()`

The continuity section is pre-formatted plain text from `build_continuity_section()` --
render it as body text with the stage header lines as h3.

---

## What NOT to change

- Function signatures of `generate_prep()`, `generate_prep_docx()`, or any `_build_*`
  functions
- `STAGE_PROFILES` dict
- Any API call logic, library seeding, debrief integration, or notification logic
- Test files -- the existing tests assert on file existence and docx readability, not
  on visual formatting. They should continue to pass without modification.

---

## Verification

After implementing:

1. Syntax check: `python -c "import scripts.phase5_interview_prep"`
2. Run existing tests: `python -m pytest tests/phase5/test_interview_prep.py -q -k "not live"`
   -- all must pass (currently 41 passing)
3. Visual check: run a dry-run generation (mock data is fine) and open the .docx to
   confirm headings, tint boxes, story blocks, and section rules render correctly

No new tests are required for this change -- formatting correctness is verified visually,
not programmatically.

---

## Key constraints

- En dashes (`\u2013`) in all body text. Never em dashes (`\u2014`).
- Never hardcode PII -- all personal data comes through the existing parameters.
- The helpers must be pure functions (take `doc` as first arg, mutate it, return nothing
  or return a Table object depending on type) -- follow whichever pattern the existing
  `generate_prep_docx()` uses for tables vs. paragraph appends.
- If a section string is empty or None, render a placeholder line rather than crashing.
