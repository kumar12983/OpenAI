# Engagement Summary Toolkit

This toolkit produces fiscal-year engagement, employee, and monthly summaries with KPI bridge, Engagement Partner, and NUI ETD enrichment.

## Contents
- fy_engagement_analysis.py — end-to-end generator (Excel + console output)
- Engagement Summary/Engagement Summary (FY).md — task/rules reference and parameters
- Bills_*.xlsx — provides Engagement Partner data (sheet: "Engagement Partners", column: Billing Partner)
- BoB_*.xlsx — provides NUI ETD data (sheet: "Export", column: NUI ETD)
- WIPs*.xlsx — main transactional WIP input (sheet: Detail by default)

## Prerequisites
- Python 3.12+ with pandas, numpy, openpyxl (already installed in .venv)
- Input files in this folder: WIPs*.xlsx, Bills_*.xlsx, BoB_*.xlsx

## Quick start
Activate the venv (PowerShell):
```powershell
& "C:\Users\sankaku\OneDrive - EY\workspace\.venv\Scripts\Activate.ps1"
```
Run the analysis (example values):
```powershell
python fy_engagement_analysis.py ^
  --input WIPs.xlsx ^
  --sheet Detail ^
  --fy-start 2025-07-01 ^
  --fy-end 2026-06-30 ^
  --billings 17M ^
  --target-margin-pct 28 ^
  --bills Bills_08.12.2025.xlsx ^
  --bob BoB_08.12.2025.xlsx ^
  --output Engagement_Summary_FY26_Final.xlsx ^
  --print-markdown
```

## Parameters (key ones)
- --input: WIP file (e.g., WIPs.xlsx)
- --sheet: transactional sheet (default Detail)
- --fy-start / --fy-end: fiscal window (YYYY-MM-DD)
- --billings: billings total (supports "20.11M")
- --target-margin-pct: target margin percent
- --bills: Bills file with sheet "Engagement Partners" (column Billing Partner → Engagement Partner)
- --bob: BoB file with sheet "Export" (column NUI ETD)
- --output: Excel output path
- --print-markdown: also print top engagement markdown to console

## What the script generates
- Engagement Summary sheet: TER-sorted, includes Engagement Partner and NUI ETD, totals row with SUBTOTAL, conditional formatting on NUI ETD (>0 red, <0 green).
- Employee Summary sheet: Level calculation, totals row with SUBTOTAL.
- Monthly Summary sheet: month-level rollup.
- KPI Totals sheet and KPI Bridge sheet: billings vs TER, margin gap, additional revenue needed.

## Rules implemented (mirrors Engagement Summary (FY).md)
- Use Accounting Date (fallback Transaction Date) within FY range.
- Expense Amount treated as pass-through revenue (included in TER).
- Metrics: ANSR, Margin Cost, TER=ANSR+Expense, Margin Amount=ANSR−Margin Cost, Margin % on ANSR.
- Engagement Partner merged from Bills; blanks backfilled via Onshore/Offshore name match.
- NUI ETD merged from BoB by Engagement ID.

## Tips
- If a file is locked (OneDrive), copy to a temp name and point --bob/--bills to it.
- Ensure header row index matches your WIP layout (default 7 is 0-based).
- You can omit --bills or --bob; those columns simply won’t appear.

## References
See Engagement Summary/Engagement Summary (FY).md for the full specification and business rules.
