# Job Search Agent — README Reformat & Backlog Re-Prioritization Brief

**Purpose:** Input for an LLM working inside the `job-search-agent` repo. Two tasks: (A) reformat `README.md` to foreground the highest-impact material, and (B) re-prioritize `context/PARKING_LOT.md`. Each directive carries a rationale, priority, and confidence so you can apply judgment rather than execute blindly.

**Source limitation — read first:** This analysis was produced from `README.md` alone. It has NOT seen `PARKING_LOT.md`, `DECISIONS_LOG.md`, the feature specs, or the code. Before acting, verify each directive against actual repo state. Where this brief and the repo disagree, the repo wins — flag the conflict to the human rather than overwriting silently.

---

## TODO (ordered by impact, highest first)

- [ ] **T1 — Add a "Results / Evidence" section to the README.** Highest leverage. Converts "looks rigorous" into "verifiably effective." (See R-1.)
- [ ] **T2 — Instrument lightweight metrics** so T1 can be populated with real numbers, not claims. (See PL-3.) T1 and T2 are coupled — do not fabricate metrics for T1; if data doesn't exist yet, do T2 first or mark samples as illustrative.
- [ ] **T3 — Lead the README with the differentiator** (engineering rigor + hallucination control), currently buried at the bottom under "Skills Demonstrated." (See R-2.)
- [ ] **T4 — Decide the README's primary audience** (portfolio reviewer vs. tool operator) and split content accordingly. This decision gates the whole reformat. (See R-3 + Open Questions.)
- [ ] **T5 — Re-prioritize the backlog:** downgrade Phase 7 (automated discovery / scraping); promote the networking/referral path. (See PL-1, PL-2.)
- [ ] **T6 — Qualify or back unmeasured claims** ("measurably improved…") until T1 supports them. (See R-5.)
- [ ] **T7 — (optional) Tighten strategic positioning** in the overview toward the defensible wedge. (See R-4.)

---

## Strategic framing (informs all edits — apply, don't paste verbatim)

The core insight driving every directive below:

> **This project optimizes the production side of a job search; the real bottleneck is the distribution side (getting seen — referrals, warm intros, escaping the ATS pile). The strongest asset in the repo is not the AI features — it is the engineering discipline wrapped around them, plus the hallucination-control design. Reformat and re-prioritize to (1) make that strength legible fast, and (2) shift future work toward the distribution bottleneck.**

Two framing facts to weave into README tone where relevant:
- **The differentiator is rigor, not novelty.** CI + two-tier test suite (mock/live) + modular shared libs + fragment-assembled docs is rare in AI portfolio projects and is the primary hire/credibility signal. **(high confidence)**
- **The defensible capability is "grounded, human-in-the-loop generation where hallucination is unacceptable."** Library-derived candidate profiling + two-layer quality checks target the exact failure mode of LLM resume tools. This is the positioning wedge worth leaning into, especially given the author's systems-engineering / defense background. **(moderate-high confidence)**

---

## Part A — README reformat directives

### R-1 — Add a "Results / Evidence" section [Priority: P1] [Confidence: high]
- **Action:** Insert a Results section immediately after Project Overview. Populate with real, specific evidence: e.g. roles processed, applications submitted, response rate, interview-advance rate, time-per-package before vs. after the tool, and/or one redacted sample output package (resume + prep). 
- **Rationale:** The README invokes "V&V framework," "requirements traceability," and claims outcomes were "measurably improved" — with zero measurements shown. For a systems-engineering audience this is the one self-inconsistency a skeptic will catch immediately. A Results section is the single highest-leverage change in the whole repo.
- **Verify:** Check whether metrics already exist (pipeline reports, tracker history in `job_pipeline.xlsx`, debrief JSON counts) before asking the human for data.
- **Acceptance:** A reviewer can judge effectiveness without running the tool, and no top-level claim is unsupported.
- **Do not:** Fabricate numbers. If real data is thin, show a redacted sample package and label aggregate figures as illustrative.

### R-2 — Lead with the differentiator [Priority: P1] [Confidence: high]
- **Action:** Rewrite the Overview (and/or add a short "Why this is built the way it is" block near the top) to foreground the engineering rigor (CI green-on-every-push, mock/live test tiers, modular design, doc-from-fragments) and the hallucination-control design (library-grounded generation, two-layer `check_*` scripts). Keep a condensed "Skills Demonstrated" but stop relying on the bottom-of-page list to carry the strongest signal.
- **Rationale:** The most impressive, most differentiating material is currently last. Reviewers skim top-down; the lead should sell the strength, not the feature inventory.
- **Acceptance:** First screen of the README communicates "this person ships maintainable, safety-conscious systems," not just "this app has many phases."

### R-3 — Resolve the dual-purpose tension (portfolio vs. manual) [Priority: P2] [Confidence: moderate-high]
- **Action:** Split content by audience. Keep a portfolio-forward narrative at the top of `README.md` (problem → differentiator → results → architecture-at-a-glance). Move deep operational content — Setup, Daily Workflow, per-phase CLI reference, Recommended Tools — below the fold or into a separate `USAGE.md` / `docs/USAGE.md`.
- **Rationale:** The README currently does double duty, and the operator-manual detail dominates the top, pushing the portfolio signal down. A 60-second skim should land a reviewer on the differentiator and results, not on `pip install` steps.
- **Verify:** Confirm with the human (Open Question Q1) before relocating large blocks; this is a structural change.
- **Do not:** Delete the operational detail — relocate it. It has real value for the operator workflow.

### R-4 — Tighten strategic positioning in the overview [Priority: P3] [Confidence: moderate]
- **Action:** Frame the project in the overview as a demonstration of grounded, human-in-the-loop LLM pipeline design for high-stakes / low-tolerance-for-error contexts — not as a generic "AI job search automation." One or two sentences; do not turn the README into a sales page.
- **Rationale:** Sharpens the credibility wedge and differentiates from the saturated "AI job tool" category.

### R-5 — Qualify unmeasured claims [Priority: P2] [Confidence: high]
- **Action:** Until R-1 lands, either back "measurably improved decision quality / outcomes" with the actual numbers or rephrase to what is demonstrable (e.g., "produces tailored, source-grounded application packages with automated quality checks"). Remove "measurably" anywhere a measurement isn't shown.
- **Rationale:** Precision-of-claim is itself part of the engineering-credibility signal this README trades on.

---

## Part B — PARKING_LOT re-prioritization directives

> Verify current contents and ordering of `context/PARKING_LOT.md` before applying. Adjust IDs/labels to match the actual file.

### PL-1 — Downgrade Phase 7 (automated role discovery / scraping) [Priority: P1] [Confidence: moderate-high]
- **Action:** Move Phase 7 (automated discovery from Google / USAJobs / ClearanceJobs) from "next / planned-priority" to "deferred / optional."
- **Rationale:** It is the least differentiated and most brittle component — scrapers break, anti-bot measures escalate, ToS/legal gray areas apply, and the time saved is marginal (manual role entry takes seconds). High maintenance cost, low strategic value. Defensible IP lives in phases 3–6.
- **Note:** If retained, scope it narrowly to sources with sanctioned APIs/feeds (e.g., USAJobs has an API) and avoid HTML scraping of ToS-restricted sites.

### PL-2 — Promote the distribution / networking path [Priority: P1] [Confidence: moderate-high]
- **Action:** Elevate expansion of Phase 6 (networking/outreach → referral and warm-intro engine) to the top of the near-term backlog.
- **Rationale:** This is the only part of the system that addresses the actual job-search bottleneck — getting seen — rather than the production of materials. Highest real-world leverage per hour of build effort. Keep the existing terminal-only / no-auto-send design (that constraint is correct and avoids LinkedIn ToS exposure).

### PL-3 — Add results instrumentation as a near-term item [Priority: P1] [Confidence: high]
- **Action:** Add a backlog item for lightweight metrics capture — counts and rates the pipeline already touches (roles processed, applied, response/advance rates, time-per-package) — written somewhere the README Results section (R-1) can draw from.
- **Rationale:** Feeds the single highest-leverage README change; doubles as a genuine V&V capability consistent with the project's stated discipline.

### PL-4 — Provider abstraction layer [Priority: P3] [Confidence: low-moderate]
- **Action:** Note (do not prioritize) an optional abstraction over the LLM provider call.
- **Rationale:** Only matters if the project is repositioned as a product or the author wants to demonstrate provider-agnostic architecture. For a single-user personal tool it is over-engineering. Keep low.

---

## Things to NOT do
- Do not fabricate metrics or sample results.
- Do not delete operational/manual content — relocate it (R-3).
- Do not expand the README's length as the goal; the objective is sharper focus, not more words.
- Do not invest further in HTML scraping (PL-1).
- Do not auto-send outreach or add auto-apply features — the human-in-the-loop / terminal-only posture is a deliberate strength.
- Do not treat this brief as ground truth over the repo; reconcile conflicts with the human.

## Open questions for the human (resolve before large structural edits)
1. **Primary README audience — portfolio reviewer or tool operator?** Gates R-3 (how aggressively to relocate manual content).
2. **Do metrics already exist** in tracker/debrief data to populate Results (R-1), or is instrumentation (PL-3/T2) a prerequisite?
3. **Is a revenue wedge an actual goal, or is this portfolio-for-hire only?** Affects how far to push R-4 positioning.

---

*Confidence legend: high = well-supported by the README's own contents and general engineering/job-search norms; moderate = reasoned judgment, repo verification advised; low = speculative, treat as a prompt for discussion. All income/market reasoning behind the positioning wedge derives from a separate 2025–2026 research pass and is directional, not guaranteed.*
