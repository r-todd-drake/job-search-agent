<!-- fragment: key_commands -->
```
# Tests (run after any script change)
pytest tests/ -m "not live" -v          # Tier 1 mock suite — all must pass
pytest -m live -v                        # Tier 2 live API (before promoting a phase)

# Pipeline
python -m scripts.pipeline_report
python -m scripts.phase2_job_ranking
python -m scripts.phase2_semantic_analyzer

# Resume generation
python -m scripts.phase4_resume_generator --stage 1 --role [role]
python -m scripts.phase4_resume_generator --stage 3 --role [role]
python -m scripts.phase4_resume_generator --stage 4 --role [role]
python -m scripts.check_resume --role [role]

# Cover letter
python -m scripts.phase4_cover_letter --stage 1 --role [role]
python -m scripts.phase4_cover_letter --stage 4 --role [role]

# Interview prep
python -m scripts.phase5_interview_prep --role [role]

# Library maintenance
python -m scripts.phase3_parse_library
python -m scripts.phase3_parse_employer "[employer name]"
python -m scripts.phase3_build_candidate_profile
python -m scripts.phase3_compile_library

# Document assembly (run after editing any fragment or template)
python scripts/utils/build_docs.py                   # rebuild all
python scripts/utils/build_docs.py --doc README.md   # rebuild one
```
