# ==============================================
# init_job_package.py
# Creates a new job package folder, empty job_description.txt,
# and a new row in jobs.csv. Opens the file for editing.
#
# Usage:
#   python -m scripts.init_job_package --role Acme_EW_SE --req REQ-12345
# ==============================================

import argparse
import csv
import os
import re
import subprocess
import sys
from datetime import date

from scripts.config import JOBS_PACKAGES_DIR as PACKAGES_DIR

JOBS_CSV = "data/jobs.csv"
ACTIVE_STATUSES = {"", "PURSUE", "CONSIDER", "APPLIED"}


def validate_role(role: str) -> None:
    if not role:
        raise ValueError("--role cannot be empty")
    if re.search(r'[/\\:*?"<>|]', role):
        raise ValueError(f"--role contains invalid characters: {role!r}")


def validate_req(req: str) -> None:
    if not req:
        raise ValueError("--req cannot be empty")


def load_csv_rows(csv_path: str) -> list:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_conflicts(rows: list, role: str, req: str) -> str | None:
    for row in rows:
        if row.get("req_number", "").strip() == req.strip():
            status = row.get("status", "").strip().upper()
            if status not in ACTIVE_STATUSES:
                return "inactive_reactivation"
            if row.get("package_folder", "").strip() == role.strip():
                return "true_duplicate"
            # same req#, different package_folder = different employer, no conflict
    return None


def create_job_folder(packages_dir: str, role: str) -> str:
    folder_path = os.path.join(packages_dir, role)
    os.makedirs(folder_path, exist_ok=False)
    return folder_path


def create_job_description(folder_path: str) -> str:
    jd_path = os.path.join(folder_path, "job_description.txt")
    with open(jd_path, "w"):
        pass
    return jd_path


def append_csv_row(csv_path: str, role: str, req: str) -> None:
    with open(csv_path, newline="", encoding="utf-8") as f:
        fieldnames = csv.DictReader(f).fieldnames or []
    row = {field: "" for field in fieldnames}
    row["package_folder"] = role
    row["req_number"] = req
    row["date_found"] = str(date.today())
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(row)


def open_file_in_editor(file_path: str) -> None:
    try:
        result = subprocess.run(["code", file_path])
        if result.returncode == 0:
            return
    except FileNotFoundError:
        pass
    try:
        if sys.platform == "win32":
            os.startfile(file_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", file_path])
        else:
            subprocess.run(["xdg-open", file_path])
        return
    except Exception:
        pass
    print(f"Warning: could not open {file_path} automatically. Open it manually.")


def main(
    role: str,
    req: str,
    packages_dir: str = PACKAGES_DIR,
    jobs_csv: str = JOBS_CSV,
    folder_creator=create_job_folder,
    file_creator=create_job_description,
    csv_appender=append_csv_row,
    file_opener=open_file_in_editor,
    folder_exists=os.path.exists,
    input_fn=input,
) -> int:
    rows = load_csv_rows(jobs_csv)
    conflict = check_conflicts(rows, role, req)

    if conflict == "true_duplicate":
        print(
            f"Error: req# {req!r} already exists in jobs.csv with an active status. "
            "No changes made."
        )
        return 1

    if conflict == "inactive_reactivation":
        print(
            f"Error: req# {req!r} exists in jobs.csv with an inactive status.\n"
            "This looks like a reactivation, not a new role.\n"
            f"To reactivate: manually move the folder from inactive/{role}/ back to "
            f"{packages_dir}/{role}/ and update the status in jobs.csv."
        )
        return 1

    final_role = role
    while folder_exists(os.path.join(packages_dir, final_role)):
        print(f"Warning: folder '{final_role}' already exists in {packages_dir}/.")
        suffix = input_fn("Enter a disambiguating suffix (e.g., '_2'): ").strip()
        if not suffix:
            print("Suffix cannot be empty. Try again.")
            continue
        final_role = role + suffix

    folder_path = folder_creator(packages_dir, final_role)
    jd_path = file_creator(folder_path)
    csv_appender(jobs_csv, final_role, req)

    print(f"\nCreated: {jd_path}")
    print("Next steps:")
    print("  1. Paste the job description text into the file above.")
    print(f"  2. Confirm the role name in the file header matches: {final_role}")

    file_opener(jd_path)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize a new job package.")
    parser.add_argument("--role", required=True, help="Role folder name (underscores, no special chars)")
    parser.add_argument("--req", required=True, help="Requisition number")
    args = parser.parse_args()

    try:
        validate_role(args.role)
        validate_req(args.req)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    sys.exit(main(args.role, args.req))
