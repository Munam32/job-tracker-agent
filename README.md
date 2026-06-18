# 🎯 Job Tracking Agent

![Python](https://img.shields.io/badge/python-3.10+-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_AI-8E75D2?style=for-the-badge&logo=google-gemini&logoColor=white)
![License](https://img.shields.io/badge/License-Apache_2.0-green?style=for-the-badge)

Turn hours of manual job tracking into automated Gmail → Google Sheets sync. 🤖

---

## ✨ Features

* **📧 Gmail Auto-Detection** — reads unread job emails, auto-updates application status in Google Sheets
* **🤖 AI Classification** — Gemini 1.5 Flash extracts company, role, and status from email content
* **⏰ Daily Scheduler** — runs automatically every day at 12:00 PM PKT (no terminal needed)
* **📝 Manual Entry** — add jobs by hand with optional JD paste for AI parsing
* **📊 Status Pipeline** — Saved → Applied → Interview Scheduled → Interviewing → Offered / Rejected / Ghosted
* **🔔 Follow-Up Reminders** — overdue reminders at a glance
* **☁️ Google Sheets Sync** — single source of truth; auto-creates "Applications" worksheet if missing

---

## 🎥 See it in Action

<!-- TODO: Replace with actual terminal recording -->
<p align="center">
  <img src="demo.gif" alt="Job Tracker Demo" width="800"/>
</p>

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Google Cloud project with **Sheets API**, **Drive API**, and **Gmail API** enabled
- Gemini API key (free from [aistudio.google.com](https://aistudio.google.com))

### 2. Install
```bash
git clone <repo-url>
cd Job_Tracker
python -m venv venv
# Windows:   venv\Scripts\activate
# Linux/mac: source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure
Set these environment variables (or edit `config.py` directly):

```bash
# Linux / macOS
export GEMINI_API_KEY="your-gemini-key"
export GOOGLE_CREDENTIALS_FILE="credentials.json"
export GMAIL_CREDENTIALS_FILE="gmail_credentials.json"
export GOOGLE_SHEET_NAME="Job Tracker"
```

```powershell
# Windows (PowerShell session)
$env:GEMINI_API_KEY="your-gemini-key"
$env:GOOGLE_CREDENTIALS_FILE="credentials.json"
$env:GMAIL_CREDENTIALS_FILE="gmail_credentials.json"
$env:GOOGLE_SHEET_NAME="Job Tracker"
```

```powershell
# Windows (persistent via setx)
setx GEMINI_API_KEY "your-gemini-key"
setx GOOGLE_CREDENTIALS_FILE "credentials.json"
setx GMAIL_CREDENTIALS_FILE "gmail_credentials.json"
setx GOOGLE_SHEET_NAME "Job Tracker"
```

<details>
<summary>📋 Detailed Google Cloud setup</summary>

1. **Sheets API** — create a Service Account → download JSON → save as `credentials.json` → create "Job Tracker" sheet → share with service account email as Editor
2. **Gmail API** — create OAuth 2.0 Client ID (Desktop app) → download JSON → save as `gmail_credentials.json` → run `python -m gmail` to authorize (creates `gmail_token.json`)
3. **Gemini** — get free API key from [Google AI Studio](https://aistudio.google.com)
</details>

### 4. Run
```bash
# First-time Gmail authorization
python -m gmail

# Manual email check (on-demand)
python agent.py check-emails

# Manual job entry
python agent.py add

# List applications
python agent.py list
python agent.py list --status Interviewing

# Update status / follow-ups
python agent.py update
python agent.py followup

# One-shot scheduler (used by auto-start)
python scheduler.py --once
```

---

## 🧠 Under the Hood

Two entry points serve the system. `agent.py` provides the CLI for manual operations (check-emails, add, list, update, followup). `scheduler.py` runs unattended via `--once` (triggered by Task Scheduler, launchd, or systemd) or as a persistent daemon. Both fetch unread job emails through `gmail.py`, classify them with `ai_parser.py` (Gemini), and sync to Google Sheets via `sheets.py` — matching by email thread ID or company+role. `sheets.py` auto-creates the "Applications" worksheet if it does not exist. All configuration flows through `config.py` from environment variables with sensible defaults.

---

## 📋 Google Sheet Layout

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

## 🔄 Status Flow

```
Saved → Applied → Interview Scheduled → Interviewing → Offered
                                               ↘ Rejected
                                               ↘ Ghosted
```

---

## 🛠 Auto-Start (Daily 12 PM PKT)

```bash
python setup_autostart.py
```

| Platform | Mechanism | Admin Required |
|---|---|---|
| Windows | Task Scheduler | Yes |
| macOS | launchd (user agent) | No |
| Linux | systemd user timer | No |

Logs at `logs/scheduler.log` (and `scheduler_error.log` for errors).

---

## ⚠️ Troubleshooting

* **Module not found** — activate your virtual environment and run `pip install -r requirements.txt`
* **Gmail auth fails** — delete `gmail_token.json` and re-run `python -m gmail`
* **Sheets not updating** — verify sheet name is exactly "Job Tracker" and is shared with the service account email as Editor
* **Emails not picked up** — adjust the `GMAIL_QUERY` filter in `config.py`

---

## ⚖️ Disclaimer

Built for personal job tracking automation. Respect API rate limits (Gemini free tier: 15 requests per minute). Use responsibly.

---

## 🤝 Contributing

Pull requests are welcome. Please open an issue first to discuss changes. This project is licensed under [Apache 2.0](LICENSE).
