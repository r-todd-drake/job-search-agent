EXAMPLE APPLICATION PACKAGE - AcmeDefense_SrSE
================================================

This folder is a complete, end-to-end example of what the pipeline
produces for one application. Every name, company, requisition number,
date, and figure in this package is FICTIONAL - the candidate is
Jane Q. Applicant, the same fixture identity used by the test suite.
No content here is derived from a real application.

The package follows the real file lifecycle documented in
context/STAGE_FILES.md. Files in pipeline order:

  job_description.txt
      Pasted JD - the starting point for every package. (Manual)

  stage1_draft.txt
      Resume draft - library-grounded bullet selection.
      (Generated: phase4_resume_generator.py --stage 1)

  stage2_approved.txt
      Human-approved resume - the source of truth for resume edits.
      (Manual edit of stage1_draft.txt)

  stage3_review.txt
      Semantic coherence review + ATS gap analysis.
      (Generated: phase4_resume_generator.py --stage 3)

  stage4_final.txt
      Final polished resume text, ready for .docx generation. (Manual)

  check_results.txt
      Two-layer quality check output - deterministic string rules plus
      API semantic assessment. (Generated: check_resume.py)

  cl_stage1_draft.txt
      Cover letter + application paragraph draft.
      (Generated: phase4_cover_letter.py --stage 1)

  cl_stage2_approved.txt
      Human-approved cover letter - source of truth. (Manual)

  cl_stage3_review.txt
      Two-layer cover letter quality check.
      (Generated: check_cover_letter.py)

  cl_stage4_final.txt
      Final cover letter text for .docx generation. (Manual)

  interview_prep_hiring_manager.txt
      Stage-calibrated interview prep package - company brief, story
      bank, gap preparation, questions to ask.
      (Generated: phase5_interview_prep.py)

  thankyou_hiring_manager_whitfield_2026-05-19.txt
      Post-interview thank-you letter, drawn from the filed debrief.
      (Generated: phase5_thankyou.py)

The structured interview debrief for this package lives at:
  example_data/debriefs/AcmeDefense_SrSE/
      debrief_hiring_manager_2026-05-18_filed-2026-05-18.json
  (Generated: phase5_debrief.py - schema in context/SCHEMA_REFERENCE.md)

NOTE ON .docx FILES
-------------------
In a real run, stage 4 of the resume and cover letter workflows and the
interview prep / thank-you scripts also emit Word documents:

  AcmeDefense_SrSE_Resume.docx
  AcmeDefense_SrSE_CoverLetter.docx
  interview_prep_hiring_manager.docx
  thankyou_hiring_manager_whitfield_2026-05-19.docx

Binary documents are intentionally not committed to this repo - the
tracked example set is plain text so every file is diffable and
reviewable. The .docx outputs are template-driven renderings of the
stage 4 text files shown here (template: templates_local/resume_template.docx,
which is gitignored as a personal binary).
