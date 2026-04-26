# Shared path and model constants for all production scripts.
# Import from here instead of defining locally in each script.

JOBS_PACKAGES_DIR = "data/job_packages"
EXPERIENCE_LIBRARY_JSON = "data/experience_library/experience_library.json"
CANDIDATE_PROFILE_PATH = "data/experience_library/candidate_profile.md"
RESUMES_DIR = "resumes"
RESUME_TEMPLATE = "templates_local/resume_template.docx"

# Sonnet for reasoning/generation; Haiku for structured data extraction (cost)
MODEL_SONNET = "claude-sonnet-4-20250514"
MODEL_HAIKU = "claude-haiku-4-5-20251001"

CONTACTS_TRACKER_PATH = "data/tracker/contact_pipeline.xlsx"
