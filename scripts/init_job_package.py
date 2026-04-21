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


if __name__ == "__main__":
    pass
