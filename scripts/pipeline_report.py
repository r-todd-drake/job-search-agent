# ==============================================
# pipeline_report.py
# Reads the job tracker and produces a summary
# report of your application pipeline status
# ==============================================

import openpyxl
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# ==============================================
# CONFIGURATION
# ==============================================

TRACKER_PATH = "data/tracker/job_pipeline.xlsx"
SHEET_NAME = "Sheet2"
REPORT_PATH = "outputs"

# ==============================================
# LOAD DATA
# ==============================================

print("Script started")
print("Loading tracker data...")

wb = openpyxl.load_workbook(TRACKER_PATH)
ws = wb[SHEET_NAME]

# Read all rows into a list of dictionaries
headers = []
applications = []

for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i == 0:
        headers = [str(cell) if cell is not None else "" for cell in row]
        continue
    if any(cell is not None for cell in row):
        app = dict(zip(headers, row))
        applications.append(app)

print(f"Loaded {len(applications)} applications")

# ==============================================
# ANALYZE DATA
# ==============================================

total = len(applications)

# Count by Status column
status_counts = {}
for a in applications:
    status = a.get("Status", "") or "Pending"
    status_counts[status] = status_counts.get(status, 0) + 1

active = status_counts.get("Active", 0)
rejected = status_counts.get("Rejected", 0)
ghosted = status_counts.get("Ghosted", 0)
closed = status_counts.get("Closed", 0)
withdrawn = status_counts.get("Withdrawn", 0)
pending = status_counts.get("Pending", 0)
offers = status_counts.get("Offer", 0)

# Interview conversion — reached interview stage
interviews_reached = sum(
    1 for a in applications
    if a.get("Reject or Interview") == "Interview"
)

# Response rate — any response received
responses = sum(1 for a in applications if a.get("First Response"))

# Salary data
salaries = []
for a in applications:
    sal = a.get("Salary (k)", "")
    if sal and isinstance(sal, str) and "$" in sal:
        try:
            parts = sal.replace("$", "").replace(",", "").split(" - ")
            low = float(parts[0])
            high = float(parts[1])
            salaries.append((low + high) / 2)
        except:
            pass
    elif isinstance(sal, (int, float)):
        salaries.append(float(sal))

# Companies with multiple applications
company_counts = {}
for a in applications:
    company = a.get("Company", "Unknown")
    company_counts[company] = company_counts.get(company, 0) + 1
repeat_companies = {k: v for k, v in company_counts.items() if v > 1}

# Active applications list
active_apps = [
    a for a in applications
    if (a.get("Status", "") or "").strip() == "Active"
]

# Response time analysis — for applications that got a response
response_times = []
for a in applications:
    applied = a.get("Applied")
    responded = a.get("First Response")
    if isinstance(applied, datetime) and isinstance(responded, datetime):
        days = (responded - applied).days
        if days >= 0:
            response_times.append(days)

# ==============================================
# PRINT REPORT
# ==============================================

print("\n" + "=" * 50)
print("       JOB SEARCH PIPELINE REPORT")
print("=" * 50)

print(f"\nOVERVIEW")
print(f"   Total Applications:      {total}")
print(f"   Received Response:       {responses}  ({round(responses/total*100)}%)")
print(f"   Reached Interview:       {interviews_reached}  ({round(interviews_reached/total*100)}%)")

print(f"\nCURRENT STATUS BREAKDOWN")
print(f"   Active:                  {active}")
print(f"   Pending:                 {pending}")
print(f"   Rejected:                {rejected}")
print(f"   Ghosted:                 {ghosted}")
print(f"   Closed:                  {closed}")
print(f"   Withdrawn:               {withdrawn}")
if offers > 0:
    print(f"   Offers:                  {offers}")

print(f"\nRESPONSE TIME (applications that received a response)")
if response_times:
    avg = round(sum(response_times) / len(response_times))
    print(f"   Average response time:   {avg} days")
    print(f"   Fastest response:        {min(response_times)} days")
    print(f"   Slowest response:        {max(response_times)} days")
    print(f"   Sample size:             {len(response_times)} applications")
else:
    print("   No response time data available")

print(f"\nSALARY RANGE (from postings with data)")
if salaries:
    print(f"   Average midpoint:        ${round(sum(salaries)/len(salaries)):,}k")
    print(f"   Lowest midpoint:         ${round(min(salaries)):,}k")
    print(f"   Highest midpoint:        ${round(max(salaries)):,}k")
    print(f"   Roles with data:         {len(salaries)} of {total}")
else:
    print("   No salary data found")

print(f"\nCOMPANIES WITH MULTIPLE APPLICATIONS")
if repeat_companies:
    for company, count in sorted(repeat_companies.items(), key=lambda x: -x[1]):
        print(f"   {company}: {count} applications")
else:
    print("   None")

print(f"\nACTIVE APPLICATIONS")
if active_apps:
    for a in active_apps:
        stage = a.get("Reject or Interview", "") or "Applied"
        print(f"   {a.get('Company')} | {a.get('Position')} | {stage}")
else:
    print("   None currently active")

print(f"\nMOST RECENT APPLICATIONS")
recent = sorted(
    [a for a in applications if a.get("Applied")],
    key=lambda x: x["Applied"],
    reverse=True
)[:5]
for a in recent:
    date = a["Applied"].strftime("%d %b %Y") if isinstance(a["Applied"], datetime) else str(a["Applied"])
    status = a.get("Status", "Pending") or "Pending"
    print(f"   {date}  |  {a.get('Company')} | {a.get('Position')} | {status}")

footer = "\n" + "=" * 50 + "\n"
footer += f"  Report generated: {datetime.now().strftime('%d %b %Y %H:%M')}\n"
footer += "=" * 50 + "\n"
print(footer)

# Save report to outputs folder
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
filename = f"pipeline_report_{timestamp}.txt"
filepath = os.path.join(REPORT_PATH, filename)

os.makedirs(REPORT_PATH, exist_ok=True)

with open(filepath, "w", encoding="utf-8") as f:
    f.write("JOB SEARCH PIPELINE REPORT\n")
    f.write(f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"OVERVIEW\n")
    f.write(f"   Total Applications:      {total}\n")
    f.write(f"   Received Response:       {responses}  ({round(responses/total*100)}%)\n")
    f.write(f"   Reached Interview:       {interviews_reached}  ({round(interviews_reached/total*100)}%)\n")
    f.write(f"\nCURRENT STATUS BREAKDOWN\n")
    f.write(f"   Active:                  {active}\n")
    f.write(f"   Pending:                 {pending}\n")
    f.write(f"   Rejected:                {rejected}\n")
    f.write(f"   Ghosted:                 {ghosted}\n")
    f.write(f"   Closed:                  {closed}\n")
    f.write(f"   Withdrawn:               {withdrawn}\n")
    if offers > 0:
        f.write(f"   Offers:                  {offers}\n")
    f.write(f"\nRESPONSE TIME\n")
    if response_times:
        f.write(f"   Average response time:   {round(sum(response_times)/len(response_times))} days\n")
        f.write(f"   Fastest response:        {min(response_times)} days\n")
        f.write(f"   Slowest response:        {max(response_times)} days\n")
        f.write(f"   Sample size:             {len(response_times)} applications\n")
    else:
        f.write("   No response time data available\n")
    f.write(f"\nSALARY RANGE\n")
    if salaries:
        f.write(f"   Average midpoint:        ${round(sum(salaries)/len(salaries)):,}k\n")
        f.write(f"   Lowest midpoint:         ${round(min(salaries)):,}k\n")
        f.write(f"   Highest midpoint:        ${round(max(salaries)):,}k\n")
        f.write(f"   Roles with data:         {len(salaries)} of {total}\n")
    f.write(f"\nACTIVE APPLICATIONS\n")
    if active_apps:
        for a in active_apps:
            stage = a.get("Reject or Interview", "") or "Applied"
            f.write(f"   {a.get('Company')} | {a.get('Position')} | {stage}\n")
    else:
        f.write("   None currently active\n")
    f.write(f"\nCOMPANIES WITH MULTIPLE APPLICATIONS\n")
    for company, count in sorted(repeat_companies.items(), key=lambda x: -x[1]):
        f.write(f"   {company}: {count} applications\n")
    f.write(f"\nMOST RECENT APPLICATIONS\n")
    for a in recent:
        date = a["Applied"].strftime("%d %b %Y") if isinstance(a["Applied"], datetime) else str(a["Applied"])
        status = a.get("Status", "Pending") or "Pending"
        f.write(f"   {date}  |  {a.get('Company')} | {a.get('Position')} | {status}\n")

print(f"Report saved to: {filepath}")