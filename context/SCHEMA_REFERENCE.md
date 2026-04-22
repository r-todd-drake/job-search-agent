# Schema Reference

JSON schemas for the three data files that drive Phase 4 and Phase 5 scripts.
These are derived from the source scripts — if a script changes a schema, update this file.

---

## Debrief JSON

**Path:** `data/debriefs/[role]/debrief_[stage]_[date]_filed-[date].json`
**Written by:** `phase5_debrief.py` (all three modes)
**Read by:** `phase5_thankyou.py`, `phase5_debrief_utils.py`

```json
{
  "metadata": {
    "role":         "string",
    "stage":        "recruiter_screen | hiring_manager | panel | final",
    "panel_label":  "string | null",
    "company":      "string | null",
    "interviewers": [
      {
        "name":   "string | null",
        "title":  "string | null",
        "notes":  "string | null"
      }
    ],
    "interview_date": "YYYY-MM-DD",
    "format":         "phone | video | onsite",
    "produced_date":  "YYYY-MM-DD"
  },
  "advancement_read": {
    "assessment": "for_sure | maybe | doubt_it | definitely_not",
    "notes":      "string | null"
  },
  "stories_used": [
    {
      "tags":       ["string"],
      "framing":    "string | null",
      "landed":     "yes | partially | no",
      "library_id": "string | null"
    }
  ],
  "gaps_surfaced": [
    {
      "gap_label":      "string | null",
      "response_given": "string | null",
      "response_felt":  "strong | adequate | weak"
    }
  ],
  "salary_exchange": {
    "range_given_min":  "int | null",
    "range_given_max":  "int | null",
    "candidate_anchor": "int | null",
    "candidate_floor":  "int | null",
    "notes":            "string | null"
  },
  "what_i_said": "string | null",
  "open_notes":  "string | null"
}
```

**Required fields:** `interview_date`, `format`, `advancement_read.assessment`,
at least one interviewer with a non-null `name`.

**Filename pattern with panel label:**
`debrief_[stage]_[panel_label]_[interview-date]_filed-[produced-date].json`

---

## Interview Library

**Path:** `data/interview_library.json`
**Written by:** `phase5_workshop_capture.py` (via `interview_library_parser.py`)
**Read by:** `interview_library_parser.py` (`get_stories`, `get_gap_responses`, `get_questions`)

```json
{
  "stories": [
    {
      "id":          "string (employer-slug–primary-tag, max 60 chars)",
      "title":       "string (raw story heading from prep doc)",
      "tags":        ["string (controlled vocabulary)"],
      "employer":    "string",
      "title_held":  "string",
      "dates":       "string",
      "situation":   "string",
      "task":        "string",
      "action":      "string",
      "result":      "string",
      "if_probed":   "string | null",
      "notes":       "string | null",
      "source":      "workshopped",
      "roles_used":  ["role-slug"],
      "last_updated": "YYYY-MM-DD"
    }
  ],
  "gap_responses": [
    {
      "id":            "string (gap-label slug, max 60 chars)",
      "gap_label":     "string",
      "severity":      "required | preferred",
      "tags":          ["string"],
      "honest_answer": "string",
      "bridge":        "string",
      "redirect":      "string",
      "notes":         "string | null",
      "source":        "workshopped",
      "roles_used":    ["role-slug"],
      "last_updated":  "YYYY-MM-DD"
    }
  ],
  "questions": [
    {
      "id":          "string (question text slug, max 60 chars)",
      "stage":       "recruiter | hiring_manager | team_panel",
      "category":    "string (first tag, or 'general' if no tags)",
      "text":        "string (question only — rationale stripped at '?')",
      "tags":        ["string"],
      "notes":       "string | null",
      "source":      "workshopped",
      "roles_used":  ["role-slug"],
      "last_updated": "YYYY-MM-DD"
    }
  ]
}
```

**Duplicate detection keys:**

- Stories: `employer` (case-insensitive) + primary tag
- Gap responses: `gap_label` (case-insensitive)
- Questions: first 60 chars of `text` (case-insensitive)

On duplicate: user is prompted to skip (roles_used updated), overwrite (roles_used merged),
or rename (new id assigned, entry appended).

**Tag vocabulary:** controlled list in `data/interview_library_tags.json` → `tags[]`.
Unknown tags are accepted with a warning.

---

## Experience Library

**Path:** `data/experience_library/experience_library.json`
**Written by:** `phase3_compile_library.py` (merges per-employer JSON + summaries.json)
**Read by:** `phase4_resume_generator.py`, `phase3_build_candidate_profile.py`

```json
{
  "metadata": {
    "last_compiled":    "YYYY-MM-DD HH:MM",
    "total_employers":  "int",
    "total_bullets":    "int",
    "total_flagged":    "int",
    "total_verify":     "int",
    "total_summaries":  "int",
    "employer_names":   ["string"]
  },
  "employers": [
    {
      "name":           "string (full employer name from ## heading)",
      "short_name":     "string (name before first '(')",
      "title":          "string (**Title:** field)",
      "dates":          "string (**Dates:** field)",
      "domain":         "string (**Domain:** field)",
      "standing_rules": ["string (> blockquote lines)"],
      "bullets": [
        {
          "id":       "string (empprefix_NNN — assigned on compile)",
          "theme":    "string (### Theme: heading)",
          "keywords": ["string (Claude-generated ATS keywords)"],
          "text":     "string ([FLAGGED]/[VERIFY] tags stripped)",
          "sources":  ["string (*Used in: ...)"],
          "notes":    ["string (*NOTE: ...)"],
          "flagged":  "bool ([FLAGGED] present in source)",
          "verify":   "bool ([VERIFY] present in source)",
          "priority": "bool (*PRIORITY: true in source)"
        }
      ]
    }
  ],
  "summaries": [
    {
      "id":       "string (summary_NNN)",
      "theme":    "string (### heading in PROFESSIONAL SUMMARIES section)",
      "text":     "string (quoted text)",
      "sources":  ["string (*Used in: ...)"],
      "keywords": ["string (Claude-generated)"],
      "flagged":  "bool"
    }
  ]
}
```

**Per-employer files:** `data/experience_library/employers/[employer_slug].json`
contain a single employer object (the same shape as one element of `employers[]` above).
These are the source-of-truth files; `experience_library.json` is compiled from them.
