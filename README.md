# Job Tracking Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-yellow.svg)]()

A CLI-based job tracking agent that reads unread job-related emails via Gmail API, classifies them using Google's Gemini AI, and syncs application status updates to Google Sheets. Also supports manual job entry for tracking applications from any source.

---

## Features

- **Gmail auto-detection** — reads unread job-related emails and auto-updates application status (e.g., "Applied" → "Interview Scheduled") in Google Sheets
- **AI-powered email classification** — uses Gemini 1.5 Flash (free tier) to extract company, role, and status from email content
- **Daily auto-scheduler** — runs the Gmail check automatically every day at 12:00 PM PKT (via system scheduler, no terminal needed)
- **Manual on-demand check** — run `python agent.py check-emails` anytime to catch up immediately
- **Manual job entry** — add jobs by hand with optional JD paste for AI parsing
- **Status tracking** — moves applications through a defined pipeline: Saved → Applied → Interview Scheduled → Interviewing → Offered / Rejected / Ghosted
- **Follow-up reminders** — view all overdue follow-ups at a glance
- **Google Sheets sync** — single source of truth accessible from anywhere
- **Auto-creates sheet** — creates "Applications" worksheet automatically if missing

---

## Quick Start

```bash
# Clone the repo
git clone <repo-url>
cd Job_Tracker

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Setup

### 1. Google Sheets API credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → enable **Google Sheets API** and **Google Drive API**
3. Create a **Service Account** → download the JSON key → save as `credentials.json` in the project root
4. Create a Google Sheet named **"Job Tracker"**
5. Share that sheet with the service account email (found in the JSON file) as **Editor**

### 2. Gmail API credentials

1. In Google Cloud Console, enable the **Gmail API**
2. Create an **OAuth 2.0 Client ID** (Desktop app) → download JSON → save as `gmail_credentials.json` in the project root
3. First run: `python -m gmail` (opens browser for authorization; creates `gmail_token.json` automatically)

### 3. Gemini API key (free)

Get your key from [Google AI Studio](https://aistudio.google.com). The free tier allows 15 requests per minute.

### 4. Set environment variables

**Linux / macOS:**
```bash
export GEMINI_API_KEY="your-gemini-key"
export GOOGLE_CREDENTIALS_FILE="credentials.json"
export GMAIL_CREDENTIALS_FILE="gmail_credentials.json"
export GOOGLE_SHEET_NAME="Job Tracker"
```

**Windows (PowerShell session):**
```powershell
$env:GEMINI_API_KEY="your-gemini-key"
$env:GOOGLE_CREDENTIALS_FILE="credentials.json"
$env:GMAIL_CREDENTIALS_FILE="gmail_credentials.json"
$env:GOOGLE_SHEET_NAME="Job Tracker"
```

**Windows (persistent via setx):**
```powershell
setx GEMINI_API_KEY "your-gemini-key"
setx GOOGLE_CREDENTIALS_FILE "credentials.json"
setx GMAIL_CREDENTIALS_FILE "gmail_credentials.json"
setx GOOGLE_SHEET_NAME "Job Tracker"
```

Alternatively, edit these values directly in `config.py`.

---

## Usage

```bash
# Check Gmail for job status updates (on-demand manual run)
python agent.py check-emails

# Add a job manually (for referrals, direct applications, etc.)
python agent.py add

# List all applications
python agent.py list

# Filter by status
python agent.py list --status Interviewing

# Update a job's status or notes
python agent.py update

# See overdue follow-up reminders
python agent.py followup

# Run email check once and exit (used by auto-start systems)
python scheduler.py --once

# Run scheduler in daemon mode (stays alive, checks daily at 12 PM)
python scheduler.py
```

---

## Auto-Start (Daily 12:00 PM Email Check)

The scheduler can run automatically every day at 12:00 PM without manual intervention. An auto-start installer is provided for all platforms.

**Requirements:**
- Virtual environment created (`python -m venv venv`)
- Dependencies installed (`venv\Scripts\pip install -r requirements.txt` on Windows, or `venv/bin/pip install -r requirements.txt` on macOS/Linux)
- First-time Gmail authentication completed (`python -m gmail`)

**Install:**

```bash
python setup_autostart.py
```

This detects your operating system and configures:

| Platform | Mechanism | Admin Required |
|----------|-----------|----------------|
| Windows  | Task Scheduler | Yes (run PowerShell as Admin) |
| macOS    | launchd (user agent) | No |
| Linux    | systemd user timer | No |

**Uninstall:**

| Platform | Command |
|----------|---------|
| Windows  | `Unregister-ScheduledTask -TaskName 'JobTracker_DailyEmailCheck' -Confirm:$false` (PowerShell Admin) |
| macOS    | `launchctl unload ~/Library/LaunchAgents/com.user.jobtracker.daily.plist && rm ~/Library/LaunchAgents/com.user.jobtracker.daily.plist` |
| Linux    | `systemctl --user disable --now jobtracker-daily.timer && rm ~/.config/systemd/user/jobtracker-daily.* && systemctl --user daemon-reload` |

**Logs:** All scheduler output is written to `logs/scheduler.log` (and `logs/scheduler_error.log` for errors).

---

```
Job_Tracker/
├── agent.py                    # CLI entry point (argparse commands)
├── ai_parser.py                # Gemini-powered JD & email parsing
├── sheets.py                   # Google Sheets read/write via gspread
├── gmail.py                    # Gmail OAuth + email fetching
├── scheduler.py                # Daily 12 PM PKT email check (--once support)
├── config.py                   # Central configuration from env vars
├── requirements.txt            # Python dependencies
├── .gitignore                  # Excludes credentials and secrets
├── LICENSE                     # Apache 2.0
├── setup_autostart.py          # Cross-platform auto-start installer
├── setup_autostart.ps1         # Windows Task Scheduler setup
├── setup_autostart_macos.sh    # macOS launchd setup
├── setup_autostart_linux.sh    # Linux systemd user timer setup
└── README.md                   # This file
```

---

## Architecture Overview

The system has two entry points. `agent.py` is the CLI interface for manual operations (check-emails, add, list, update, followup). `scheduler.py` is designed for unattended use — it runs `--once` for one-shot execution (invoked by system schedulers) or in daemon mode for persistent background operation. Both use `gmail.py` to fetch unread job-related emails and `ai_parser.py` to classify them via Gemini, extracting company, role, and status. Matched applications are updated in Google Sheets via `sheets.py`; unmatched ones create new rows. `sheets.py` auto-creates the "Applications" worksheet if it does not exist. All configuration flows through `config.py`, which reads environment variables with sensible defaults.

---

## Google Sheet Layout

The agent auto-creates a worksheet named **"Applications"** with these columns:

| Column | Description |
|---|---|
| Company | Company name |
| Role | Job title |
| Url | Job posting link |
| Location | City or Remote |
| Salary | Salary info if available |
| Skills Required | AI-extracted skills list |
| Status | Saved → Applied → Interview Scheduled → Interviewing → Offered / Rejected / Ghosted |
| Date Applied | YYYY-MM-DD |
| Last Follow Up | Date of last follow-up |
| Next Follow Up | Scheduled follow-up date |
| Notes | Free-form notes |
| Email Thread ID | Gmail thread ID for auto-matching |

---

## Status Flow

```
Saved → Applied → Interview Scheduled → Interviewing → Offered
                                              ↘ Rejected
                                              ↘ Ghosted
```

---

## Troubleshooting

**"Module not found" errors**
Ensure your virtual environment is activated and dependencies are installed: `pip install -r requirements.txt`.

**Gmail authorization fails**
Delete `gmail_token.json` and re-run `python -m gmail` to trigger a fresh browser-based OAuth flow.

**Google Sheets not updating**
Verify the sheet is named exactly "Job Tracker" (case-sensitive) and has been shared with the service account email as Editor.

**Emails not being picked up**
Check the `GMAIL_QUERY` in `config.py` — it searches for unread emails matching interview/offer/rejection subjects and common recruiter senders. Adjust the query if your emails use different patterns.

**No new applications created from emails**
The email classifier uses Gemini AI. If the AI returns low confidence or null, the email is skipped. Check `logs/scheduler.log` for details.

---

## Testing

No automated test suite is currently available. Manual verification is recommended after each change:

```bash
# Verify manual add with AI parsing
python agent.py add

# Verify Gmail detection
python agent.py check-emails

# Verify one-shot scheduler mode
python scheduler.py --once
```

---

## Contributing

Contributions are welcome. Please open an issue first to discuss changes. This project uses [Apache 2.0](LICENSE) licensing.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Commit your changes (`git commit -am 'Add my change'`)
4. Push the branch (`git push origin feature/my-change`)
5. Open a Pull Request
