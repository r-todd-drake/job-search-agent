This folder contains the job search tracker spreadsheet.

Expected filename: job_pipeline_example.xlsx

The tracker is an Excel workbook with the following schema (Sheet2):

Column A — Company
Column B — Position
Column C — Link
Column D — REQ (job requisition number)
Column E — Salary (k) — format: "$130 - $221" or numeric
Column F — Recruiter
Column G — Applied (date)
Column H — First Response (date)
Column I — Reject or Interview
Column J — Interview 1 (date)
Column K — Interview 2 (date)
Column L — Interview 3 (date)
Column M — Interview 4 (date)
Column N — Notes
Column O — Status: Active / Rejected / Ghosted / Closed / Withdrawn / Offer / blank=Pending
Column P — Resume Version (e.g. "AeroDefense_SrSE")

Dates should be formatted as standard Excel dates.
The pipeline_report.py script reads Sheet2 only.
Sheet1 can be used for a prior search cycle if desired.