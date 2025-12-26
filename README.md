# OpenAI

AI Generated Engagement Summary based on User Requirements.

## Quick Start

### 1) Prerequisites
- Python 3.9+ (recommended)
- Access to the SharePoint site/library you want to read from / write to (if using SharePoint integration)

> Note: This repo currently does not include a `requirements.txt` or `pyproject.toml`. If your scripts import third‑party packages (e.g., pandas, requests, office365/SharePoint libs, openai, etc.), install them as needed for your environment.

### 2) Clone the repo
```bash
git clone https://github.com/kumar12983/OpenAI.git
cd OpenAI
```

### 3) Create a virtual environment (recommended)
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 4) Configure the workflow + SharePoint
Configuration templates are provided here:

- `Engagement Summary AI/src/config/workflow_config.json.template`
- `Engagement Summary AI/src/config/sharepoint_config.json.template`

Copy the templates to real config files (and fill in your values):

```bash
cp "Engagement Summary AI/src/config/workflow_config.json.template"  "Engagement Summary AI/src/config/workflow_config.json"
cp "Engagement Summary AI/src/config/sharepoint_config.json.template" "Engagement Summary AI/src/config/sharepoint_config.json"
```

Then edit:
- `workflow_config.json` to match your engagement summary workflow options
- `sharepoint_config.json` with your SharePoint connection/site/library settings (and credentials as required by your org)

**Security note:** do not commit real credentials. Keep local configs untracked (recommend adding them to `.gitignore`).

### 5) Run the engagement analysis
Use the automation entrypoint:

```bash
python "Engagement Summary AI/src/automate/run_engagement_analysis.py"
```

### 6) Where to look in the code
Core modules:
- `Engagement Summary AI/src/automate/run_engagement_analysis.py`  
  Orchestrates the end-to-end run (recommended entrypoint).
- `Engagement Summary AI/src/analyze/fy_engagement_analysis.py`  
  Main engagement analysis logic.
- `Engagement Summary AI/src/analyze/prepare_bills.py` / `prepare_bob.py`  
  Data preparation steps.
- `Engagement Summary AI/src/automate/sharepoint_integration.py`  
  SharePoint integration (download/upload or syncing).

## Project Layout

```text
.
├── README.md
└── Engagement Summary AI/
    ├── LLM/
    ├── docs/
    └── src/
        ├── analyze/
        │   ├── fy_engagement_analysis.py
        │   ├── prepare_bills.py
        │   └── prepare_bob.py
        ├── automate/
        │   ├── run_engagement_analysis.py
        │   └── sharepoint_integration.py
        └── config/
            ├── sharepoint_config.json.template
            └── workflow_config.json.template
```

## Troubleshooting

### Config file not found
If you see errors about missing config files, confirm you created:
- `Engagement Summary AI/src/config/workflow_config.json`
- `Engagement Summary AI/src/config/sharepoint_config.json` (if using SharePoint)

### Permission / authentication failures (SharePoint)
Double-check:
- site/library URLs
- tenant/domain values
- auth method required by your organization
- your account permissions on the target SharePoint location
