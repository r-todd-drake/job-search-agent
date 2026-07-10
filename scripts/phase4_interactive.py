# scripts/phase4_interactive.py

import os
import sys
import shutil
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

from scripts.config import JOBS_PACKAGES_DIR, EXPERIENCE_LIBRARY_JSON, RESUMES_DIR
from scripts.phase4_resume_generator import (
    run_stage1,
    run_stage3,
    stage4_generate_docx,
    load_jd,
    load_library,
    load_candidate_profile,
)

load_dotenv()


def list_eligible_roles(jobs_dir=JOBS_PACKAGES_DIR):
    """Return sorted role names that have job_description.txt, excluding inactive/."""
    base = Path(jobs_dir)
    if not base.exists():
        return []
    return sorted(
        folder.name
        for folder in base.iterdir()
        if folder.is_dir()
        and folder.name != "inactive"
        and (folder / "job_description.txt").exists()
    )


def open_file(path):
    """Open path with the system default application."""
    if sys.platform == "win32":
        os.startfile(str(path))
    elif sys.platform == "darwin":
        import subprocess
        subprocess.Popen(["open", str(path)])
    else:
        import subprocess
        subprocess.Popen(["xdg-open", str(path)])


def main():
    print("=== Phase 4 Interactive Resume Generator ===\n")

    if not os.path.exists(EXPERIENCE_LIBRARY_JSON):
        print(
            "experience_library.json not found. Run:\n"
            "  python -m scripts.phase3_compile_library\n"
            "Then re-run phase4_interactive.py."
        )
        sys.exit(1)

    roles = list_eligible_roles(JOBS_PACKAGES_DIR)
    if not roles:
        print(
            "No job packages with a job_description.txt were found in data/job_packages/.\n"
            "Create one first: python -m scripts.init_job_package --role [name]"
        )
        sys.exit(1)

    print("Available roles:")
    for i, role in enumerate(roles, 1):
        print(f"  {i}. {role}")
    print()

    while True:
        choice = input("Enter role number or folder name: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(roles):
            role = roles[int(choice) - 1]
            break
        if choice in roles:
            role = choice
            break
        print("Not found – try again.")

    print(f"\nSelected: {role}\n")

    package_dir = Path(JOBS_PACKAGES_DIR) / role
    stage1_path = package_dir / "stage1_draft.txt"
    stage2_path = package_dir / "stage2_approved.txt"
    stage3_path = package_dir / "stage3_review.txt"
    stage4_path = package_dir / "stage4_final.txt"
    jd_path = package_dir / "job_description.txt"

    jd_text = load_jd(str(jd_path))
    library = load_library()
    candidate_profile = load_candidate_profile()
    client = Anthropic()

    # Stage 1
    print("Running Stage 1 – selecting resume bullets...")
    print("(This may take 30–60 seconds)\n")
    try:
        run_stage1(client, jd_text, library, candidate_profile, str(stage1_path))
    except Exception as e:
        print(
            f"Stage 1 failed: {e}\n\n"
            "This is usually caused by:\n"
            "  - Invalid or expired ANTHROPIC_API_KEY in .env\n"
            "  - No internet connection\n"
            "  - Missing input file\n\n"
            "No files were changed. Fix the issue and run phase4_interactive.py again."
        )
        sys.exit(1)

    print(f"Stage 1 complete. Draft saved to:\n  {stage1_path}\n")
    print("Opening in your default text editor...")
    try:
        open_file(stage1_path)
    except OSError:
        print(f"Could not open the file automatically. Open it manually:\n  {stage1_path}")

    input(
        "\nReview the draft. Add, remove, or swap bullets as needed.\n"
        "When you are satisfied, save your edits AS stage2_approved.txt in your editor\n"
        "(or just save stage1_draft.txt in place if no changes are needed), then press Enter here.\n\n"
        "Press Enter when done reviewing: "
    )

    if stage2_path.exists():
        print("Using the stage2_approved.txt you saved.\n")
    else:
        shutil.copy2(stage1_path, stage2_path)
        print("stage2_approved.txt not found - copied stage1_draft.txt as the approved version.\n")

    # Stage 3 loop
    while True:
        print("Running Stage 3 – semantic review and wording suggestions...")
        print("(This may take 20–40 seconds)\n")
        stage2_text = stage2_path.read_text(encoding="utf-8")
        try:
            run_stage3(client, stage2_text, jd_text, str(stage3_path))
        except Exception as e:
            print(
                f"Stage 3 failed: {e}\n\n"
                "This is usually caused by:\n"
                "  - Invalid or expired ANTHROPIC_API_KEY in .env\n"
                "  - No internet connection\n"
                "  - Missing input file\n\n"
                "No files were changed. Fix the issue and run phase4_interactive.py again."
            )
            sys.exit(1)

        print(f"Stage 3 review complete. Suggestions saved to:\n  {stage3_path}\n")
        print("Opening in your default text editor...")
        try:
            open_file(stage3_path)
        except OSError:
            print(f"Could not open the file automatically. Open it manually:\n  {stage3_path}")

        print(
            "\nReview the suggestions and decide which to accept.\n"
            "Apply accepted changes to stage2_approved.txt in your editor.\n\n"
            "When done, choose an option:\n"
            "  [a] Accept – save as stage4_final.txt and generate the resume\n"
            "  [r] Re-run Stage 3 on updated stage2_approved.txt\n"
        )
        while True:
            choice = input("Enter choice (a/r): ").strip().lower()
            if choice in ("a", "r"):
                break
            print("Enter 'a' or 'r'.")

        if choice == "a":
            break

        input(
            "\nMake your edits to stage2_approved.txt now, save the file in your editor,\n"
            "then press Enter here to re-run the Stage 3 analysis.\n\n"
            "Press Enter when ready: "
        )

    # Stage 4
    print("\nSaving stage4_final.txt...")
    shutil.copy2(stage2_path, stage4_path)

    print("Running Stage 4 – generating resume document...")
    final_content = stage4_path.read_text(encoding="utf-8")
    output_path = stage4_generate_docx(final_content, role, os.path.join(RESUMES_DIR, role))

    print(f"\nResume generated:\n  {output_path}\n")
    print("Opening in your default application...")
    try:
        open_file(output_path)
    except OSError:
        print(f"Could not open the file automatically. Open it manually:\n  {output_path}")

    input(
        "\nReview the formatted document. When you are ready to close out, press Enter here.\n\n"
        "Press Enter to finish: "
    )

    print(
        f"\n=== Phase 4 Complete ===\n"
        f"Resume: {output_path}\n\n"
        "Next steps:\n"
        "  - Export the resume to PDF in LibreOffice (File > Export as PDF)\n"
        "  - Update jobs.csv status to APPLIED after submitting\n"
        f"  - Generate a cover letter: python -m scripts.phase4_cover_letter"
        f" --stage 1 --role {role}\n"
        f"  - Set up networking outreach: python -m scripts.phase6_networking"
        f" --contact \"[name]\" --stage 1"
    )


if __name__ == "__main__":
    main()
