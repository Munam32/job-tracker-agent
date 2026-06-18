# Job Tracking Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-yellow.svg)]()

A CLI-based job tracking agent that scrapes listings from LinkedIn, Indeed, Rozee.pk, and direct URLs, parses job descriptions using Google's Gemini AI, syncs everything to Google Sheets, and automatically updates application status from Gmail emails.

---

## Features

- **Multi-source scraping** — scrapes job listings from LinkedIn, Indeed, Rozee.pk, or any direct URL
- **AI-powered JD parsing** — extracts job title, required skills, salary range, and summary from job descriptions using Gemini 1.5 Flash (free tier)
- **Gmail auto-detection** — reads unread job-related emails and auto-updates application status (e.g., "Applied" → "Interview Scheduled") in Google Sheets
- **Daily scheduler** — runs the Gmail check automatically every day at 12:00 PM PKT via APScheduler
- **Manual job entry** — add jobs by hand with optional JD paste for AI parsing
- **Status tracking** — moves applications through a defined pipeline: Saved → Applied → Interview Scheduled → Interviewing → Offered / Rejected / Ghosted
- **Follow-up reminders** — view all overdue follow-ups at a glance
- **Google Sheets sync** — single source of truth accessible from anywhere

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
# Check Gmail for job status updates (manual)
python agent.py check-emails

# Add a job manually
python agent.py add

# Scrape job listings
python agent.py scrape

# List all applications
python agent.py list

# Filter by status
python agent.py list --status Interviewing

# Update a job's status or notes
python agent.py update

# See overdue follow-up reminders
python agent.py followup

# Run the daily scheduler (12:00 PM PKT)
python scheduler.py
```

---

## Project Structure

```
Job_Tracker/
├── agent.py          # CLI entry point (argparse commands)
├── scraper.py        # Web scraping (LinkedIn, Indeed, Rozee.pk, URLs)
├── ai_parser.py      # Gemini-powered JD parsing
├── sheets.py         # Google Sheets read/write via gspread
├── gmail.py          # Gmail OAuth + email parsing
├── scheduler.py      # APScheduler daily 12 PM PKT trigger
├── config.py         # Central configuration from env vars
├── requirements.txt  # Python dependencies
├── .gitignore        # Excludes credentials and secrets
├── LICENSE           # Apache 2.0
└── README.md         # This file
```

---

## Architecture Overview

The user invokes `agent.py`, which delegates to specialized modules. `scraper.py` fetches job listings from configured sources and passes raw descriptions to `ai_parser.py`, which uses Gemini to extract structured fields (title, skills, salary, summary). Structured data is written to Google Sheets via `sheets.py`. Separately, `gmail.py` reads unread job-related emails, matches them against existing sheet rows by thread ID, and updates the status column (e.g., "Applied" → "Interview Scheduled"). `scheduler.py` wraps the Gmail check with APScheduler for daily unattended execution at 12:00 PM PKT. All configuration flows through `config.py`, which reads environment variables with sensible defaults.

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

**Scraping fails for LinkedIn / Indeed**
These platforms actively block automated scrapers. If scraping returns no results, use `python agent.py add` with a direct job URL instead.

**"Module not found" errors**
Ensure your virtual environment is activated and dependencies are installed: `pip install -r requirements.txt`.

**Gmail authorization fails**
Delete `gmail_token.json` and re-run `python -m gmail` to trigger a fresh browser-based OAuth flow.

**Google Sheets not updating**
Verify the sheet is named exactly "Job Tracker" (case-sensitive) and has been shared with the service account email as Editor.

---

## Testing

No automated test suite is currently available. Manual verification is recommended after each change:

```bash
# Verify scraping works
python agent.py scrape --source url --url "https://example.com/job"

# Verify manual add with AI parsing
python agent.py add

# Verify Gmail detection
python agent.py check-emails

# Verify scheduler starts
python scheduler.py
```

---

## Contributing

Contributions are welcome. Please open an issue first to discuss changes. This project uses [Apache 2.0](LICENSE) licensing.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Commit your changes (`git commit -am 'Add my change'`)
4. Push the branch (`git push origin feature/my-change`)
5. Open a Pull Request
