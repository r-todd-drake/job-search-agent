Capability 1: Job Pipeline Reporting
  Description: Generate metrics and status summary from application tracker
  Components: scripts/pipeline_report.py, data/tracker/job_pipeline.xlsx
  Verification: Run script, confirm output matches tracker data
  Status: ✅ Verified

Capability 2: Job Ranking and Scoring
  Description: Score and rank job postings against candidate keyword profile
  Components: scripts/phase2_job_ranking.py, data/jobs.csv, data/job_packages/
  Verification: Run script against example_data, confirm ranked output
  Status: ✅ Verified

Capability 3: Semantic Fit Analysis
  ...