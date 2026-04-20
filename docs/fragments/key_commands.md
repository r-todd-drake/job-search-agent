<!-- fragment: key_commands -->
```
# Tests (run after any script change)
pytest tests/ -m "not live" -v          # Tier 1 mock suite — all 73 must pass
pytest -m live -v                        # Tier 2 live API (before promoting a phase)

# Pipeline
python scripts/pipeline_report.py
python scripts/phase2_job_ranking.py
python scripts/phase2_semantic_analyzer.py

# Resume generation
python scripts/phase4_resume_generator.py --stage 1 --role [role]
python scripts/phase4_resume_generator.py --stage 3 --role [role]
python scripts/phase4_resume_generator.py --stage 4 --role [role]
python scripts/check_resume.py --role [role]

# Cover letter
python scripts/phase4_cover_letter.py --stage 1 --role [role]
python scripts/phase4_cover_letter.py --stage 4 --role [role]

# Interview prep
python scripts/phase5_interview_prep.py --role [role]

# Library maintenance
python scripts/phase3_parse_library.py
python scripts/phase3_parse_employer.py "[employer name]"
python scripts/phase3_build_candidate_profile.py
python scripts/phase3_compile_library.py
```
