# Job Search Agent — Setup Guide

**How to use this file:** Copy the prompt block in Section 1 and paste it into Claude.ai (the free tier works). Claude.ai will walk you through the rest interactively, asking questions along the way. Follow its instructions step by step.

---

## Section 1 — Paste this into Claude.ai

```
I need your help setting up a Python-based job search automation tool on my computer.
I will follow your instructions step by step. Please ask me one question at a time
to confirm each step worked before moving to the next one.

Start by asking what operating system I am using (Windows, Mac, or Linux).

Here is what we need to accomplish together, in order:

1. Confirm Python 3.10 or newer is installed. If not, walk me through installing it.
2. Open a terminal in the project folder and run: pip install -r requirements.txt
   Confirm the install succeeded.
3. Walk me through creating the .env file from the .env.example template.
   Explain each variable one at a time. Tell me where to get the Anthropic API key.
   Important: instruct me to edit the .env file directly — never ask me to paste
   API keys or personal information into this conversation.
4. Walk me through creating context/candidate/candidate_config.yaml from the example file.
   Tell me I can run this command to fill it in interactively:
     python -m scripts.init_candidate
   Or I can open the file in a text editor and follow the comments.
5. Explain that the experience library is where the tool stores resume bullets as
   structured data. Tell me I need to create
   data/experience_library/experience_library.md with my work history.
   Offer to help me understand the format (I can ask about it separately).
   After I create it, walk me through running these three commands in order:
     python -m scripts.phase3_parse_library
     python -m scripts.phase3_build_candidate_profile
     python -m scripts.phase3_compile_library
6. Walk me through a first run using Phase 2 job ranking:
   a. Add one job description to data/jobs.csv
   b. Run: python -m scripts.init_job_package --role [role_name]
   c. Paste the job description text into the created job_description.txt file
   d. Run: python -m scripts.phase2_job_ranking
   e. Run: python -m scripts.phase2_semantic_analyzer
   Confirm that an output file appeared in the outputs/ folder.
7. Once I confirm there is output in the outputs/ folder, tell me setup is complete
   and give me a brief plain-English summary of what each phase of the tool does
   (Phase 2 through Phase 6).
```

---

## Section 2 — What Claude.ai will not do for you

These steps require your own input and cannot be automated:

- **Writing your experience library** (`data/experience_library/experience_library.md`):
  This is a structured document with your work history in bullet format. It takes
  time to write and must come from you. Claude.ai can explain the format and help
  you draft it if you paste your resume into the conversation.

- **Writing your intro monologue and short-tenure explanation** in `candidate_config.yaml`:
  These are multi-paragraph blocks that require your voice and career narrative.
  The setup wizard (`init_candidate.py`) will leave placeholder text and tell you
  where to fill them in.

- **Obtaining your Anthropic API key**: Go to console.anthropic.com, sign in,
  and create an API key. Paste it into your `.env` file — never into Claude.ai.

---

## Section 3 — Confirming setup is complete

Setup is complete when this command runs without errors and produces a file in `outputs/`:

```
python -m scripts.phase2_semantic_analyzer --role [your_role_name]
```

If you see a file appear in the `outputs/` folder with a semantic fit analysis, you are ready to use the full pipeline.

---

## Section 4 — What each phase does

- **Phase 2:** Scores and ranks job descriptions. Run this when you add a new job posting.
- **Phase 3:** Builds your experience library. Run this once, then update when you add bullets.
- **Phase 4:** Generates a tailored resume for a specific role. Run interactively with `python -m scripts.phase4_interactive`.
- **Phase 5:** Creates an interview prep package when you have an interview scheduled.
- **Phase 6:** Generates professional networking outreach messages.
