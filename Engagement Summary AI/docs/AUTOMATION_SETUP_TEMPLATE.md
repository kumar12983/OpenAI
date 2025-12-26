# Engagement Analysis Automation - Setup Guide

## Overview
This solution automates the complete engagement analysis workflow:
1. **Download** input files (WIPs, Bills, BoB) from SharePoint
2. **Prepare** Bills and BoB files (extract IDs, calculate billings)
3. **Analyze** engagement data and generate KPI reports
4. **Upload** results to SharePoint
5. **Notify** team members via email

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SharePoint (Input)                      │
│  WIPs.xlsx  │  Bills_*.xlsx  │  BoB_*.xlsx                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ Download (Graph API)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Local Processing                           │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐     │
│  │ prepare_    │  │ prepare_    │  │ fy_engagement_   │     │
│  │ bills.py    │  │ bob.py      │  │ analysis.py      │     │
│  └─────────────┘  └─────────────┘  └──────────────────┘     │
│         │                │                    │             │
│         └────────────────┴────────────────────┘             │
│                          │                                  │
│              Engagement_Summary_FY26.xlsx                   │
└──────────────────────┬──────────────────────────────────────┘
                       │ Upload (Graph API)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    SharePoint (Output)                      │
│           Engagement_Summary_FY26_YYYYMMDD.xlsx             │
│                          +                                  │
│                 Email Notification                          │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### 1. Python Environment
```powershell
# Python 3.12+ with required packages
pip install pandas numpy openpyxl msal requests
```

### 2. Azure AD App Registration

#### Option A: Delegated (Interactive) Authentication
Best for: Manual runs, testing

1. Go to [Azure Portal](https://portal.azure.com) > Azure Active Directory > App registrations
2. Click "New registration"
   - Name: "Engagement Analysis Automation"
   - Supported account types: "Accounts in this organizational directory only"
   - Redirect URI: Public client/native > `http://localhost`
3. Note the **Application (client) ID** and **Directory (tenant) ID**
4. Go to "API permissions"
   - Add permission > Microsoft Graph > Delegated permissions
   - Add: `Files.ReadWrite.All`, `Sites.ReadWrite.All`, `Mail.Send`
   - Click "Grant admin consent"

#### Option B: App-Only (Client Credentials) Authentication
Best for: Scheduled/unattended automation

1. Follow steps 1-4 from Option A
2. Use **Application permissions** instead of Delegated
   - Add: `Files.ReadWrite.All`, `Sites.ReadWrite.All`, `Mail.Send`
3. Go to "Certificates & secrets"
   - Click "New client secret"
   - Set expiration (e.g., 24 months)
   - Copy the **secret value** immediately (you won't see it again)

### 3. SharePoint Setup

1. Create SharePoint folders:
   ```
   Shared Documents/
   ├── Engagement Analysis/
   │   ├── Inputs/       # Place WIPs, Bills, BoB files here
   │   └── Outputs/      # Automated results will be uploaded here
   ```

2. Ensure your app has access:
   - Site Settings > Site Permissions > Grant access to the app

## Configuration

### 1. SharePoint Configuration

Copy the template and fill in your details:
```powershell
Copy-Item sharepoint_config.json.template sharepoint_config.json
```

Edit `sharepoint_config.json`:
```json
{
  "tenant_id": "your-tenant-id-from-azure",
  "client_id": "your-client-id-from-app-registration",
  "client_secret": "your-client-secret (only for app-only auth)",
  "sharepoint_domain": "yourcompany.sharepoint.com",
  "scopes": [
    "https://graph.microsoft.com/Files.ReadWrite.All",
    "https://graph.microsoft.com/Sites.ReadWrite.All",
    "https://graph.microsoft.com/Mail.Send"
  ]
}
```

### 2. Workflow Configuration

Copy the template and customize:
```powershell
Copy-Item workflow_config.json.template workflow_config.json
```

Edit `workflow_config.json`:
```json
{
  "auth_type": "delegated",  // or "app" for automation
  
  "downloads": {
    "site_name": "YourTeamSite",
    "folder_path": "Shared Documents/Engagement Analysis/Inputs",
    "wips_pattern": "WIPs",
    "bills_pattern": "Bills_",
    "bob_pattern": "BoB_"
  },
  
  "analysis": {
    "fy_start": "2025-07-01",
    "fy_end": "2026-06-30",
    "invoice_month_from": "2025-08",
    "target_margin_pct": 28
  },
  
  "uploads": {
    "site_name": "YourTeamSite",
    "folder_path": "Shared Documents/Engagement Analysis/Outputs"
  },
  
  "notification": {
    "enabled": true,
    "recipients": [
      "analyst1@yourcompany.com",
      "manager@yourcompany.com"
    ]
  }
}
```

## Usage

### Manual Execution

```powershell
# Activate virtual environment
& "C:\Users\sankaku\OneDrive - EY\workspace\.venv\Scripts\Activate.ps1"

# Run the workflow
python run_engagement_analysis.py --config workflow_config.json
```

### Scheduled Automation (Windows Task Scheduler)

#### Create a batch file for execution:
Create `run_analysis.bat`:
```batch
@echo off
cd /d "C:\Users\sankaku\OneDrive - EY\workspace"
call .venv\Scripts\activate.bat
python run_engagement_analysis.py --config workflow_config.json
pause
```

#### Schedule the task:
```powershell
# Weekly on Monday at 6:00 AM
schtasks /create /tn "EngagementAnalysis-Weekly" `
  /tr "C:\Users\sankaku\OneDrive - EY\workspace\run_analysis.bat" `
  /sc weekly /d MON /st 06:00 `
  /ru "SYSTEM"

# Or monthly on the 1st at 8:00 AM
schtasks /create /tn "EngagementAnalysis-Monthly" `
  /tr "C:\Users\sankaku\OneDrive - EY\workspace\run_analysis.bat" `
  /sc monthly /d 1 /st 08:00 `
  /ru "SYSTEM"
```

#### Verify scheduled task:
```powershell
schtasks /query /tn "EngagementAnalysis-Weekly" /fo LIST /v
```

## Workflow Steps

When you run `python run_engagement_analysis.py`, it executes:

1. **Authentication** - Connects to SharePoint via Microsoft Graph API
2. **Download** - Fetches latest WIPs, Bills, BoB files from SharePoint
3. **Prepare Bills** - Extracts Engagement IDs, calculates billing amounts, filters from Aug 2025
4. **Prepare BoB** - Extracts Engagement IDs, validates required columns
5. **Analysis** - Runs engagement summary with KPI bridge, creates Excel workbook
6. **Upload** - Pushes result file to SharePoint Outputs folder
7. **Notify** - Sends email to team with shareable link
8. **Cleanup** - Optionally removes temporary work files

## Troubleshooting

### Authentication Issues

**Error:** `AADSTS50011: The reply URL specified in the request does not match`
- Solution: Add `http://localhost` as redirect URI in App Registration

**Error:** `Insufficient privileges to complete the operation`
- Solution: Grant admin consent for API permissions in Azure Portal

### SharePoint Access Issues

**Error:** `Worksheet named 'Export' not found`
- Solution: Verify BoB file has an "Export" sheet

**Error:** `Access denied`
- Solution: Ensure app has permissions to the SharePoint site

### File Not Found

**Error:** `No files matching 'WIPs' found`
- Solution: Check folder path and file patterns in `workflow_config.json`

### Schedule Issues

**Task doesn't run:**
- Check Task Scheduler event logs (Event Viewer > Task Scheduler)
- Verify service account has permission to run Python
- Test batch file manually first

## Testing

### Test SharePoint Integration
```powershell
# Test download
python sharepoint_integration.py --download "YourSite:Inputs:WIPs.xlsx"

# Test upload
python sharepoint_integration.py --upload "YourSite:Outputs:test.xlsx"
```

### Test Individual Steps
```powershell
# Test Bills preparation
python prepare_bills.py --input Bills_08.12.2025.xlsx --output Bills_test.xlsx

# Test BoB preparation
python prepare_bob.py --input BoB_08.12.2025.xlsx --output BoB_test.xlsx

# Test analysis
python fy_engagement_analysis.py `
  --input WIPs.xlsx `
  --bills Bills_test.xlsx `
  --bob BoB_test.xlsx `
  --output test_output.xlsx
```

## Security Best Practices

1. **Never commit secrets to Git**
   - Add `sharepoint_config.json` and `workflow_config.json` to `.gitignore`
   - Use templates (`.template` files) for version control

2. **Use app-only auth for production**
   - More secure for unattended automation
   - Set client secret expiration reminder

3. **Limit API permissions**
   - Only grant minimum required permissions
   - Use least-privilege principle

4. **Rotate credentials regularly**
   - Update client secrets before expiration
   - Review app permissions quarterly

## Support

For issues or questions:
1. Check logs in `./work` directory
2. Review error messages in terminal output
3. Verify SharePoint and Azure configurations
4. Contact IT support for permission issues

## Files Reference

| File | Purpose |
|------|---------|
| `sharepoint_integration.py` | SharePoint Graph API client |
| `run_engagement_analysis.py` | Main orchestrator script |
| `prepare_bills.py` | Bills file preparation |
| `prepare_bob.py` | BoB file preparation |
| `fy_engagement_analysis.py` | Engagement analysis engine |
| `sharepoint_config.json` | SharePoint authentication config |
| `workflow_config.json` | Workflow execution config |
| `AUTOMATION_SETUP.md` | This file |
