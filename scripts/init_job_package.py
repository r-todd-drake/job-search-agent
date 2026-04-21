# ==============================================
# init_job_package.py
# Creates a new job package folder, empty job_description.txt,
# and a new row in jobs.csv. Opens the file for editing.
#
# Usage:
#   python -m scripts.init_job_package --role Anduril_EW_SE --req REQ-12345
# ==============================================

import argparse
import csv
import os
import re
import subprocess
import sys
from datetime import date

JOBS_CSV = "data/jobs.csv"
PACKAGES_DIR = "data/job_packages"
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


if __name__ == "__main__":
    pass
