# 🎯 Job Tracking Agent

A CLI-based job tracking agent that scrapes listings, parses JDs with AI, syncs to Google Sheets, and auto-updates application status from Gmail emails.

---

## Features

| Feature | Details |
|---|---|
| **Scrape** | LinkedIn, Indeed, Rozee.pk, or any direct URL |
| **AI Parsing** | Extracts title, skills, salary, summary from JDs via **Gemini (free)** |
| **Gmail Integration** | Reads unread job emails, auto-updates status in Sheets |
| **Scheduler** | Daily 12:00 PM PKT automated email check |
| **Manual Add** | Add jobs manually + optional JD paste |
| **Track Status** | Saved → Applied → Interview Scheduled → Interviewing → Offered / Rejected / Ghosted |
| **Follow-ups** | See all overdue follow-ups at a glance |
| **Google Sheets** | Single source of truth, accessible anywhere |

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Google Sheets API credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Google Sheets API** and **Google Drive API**
3. Create a **Service Account** → Download the JSON key → save as `credentials.json` in this folder
4. Create a Google Sheet named **"Job Tracker"**
5. Share that sheet with the service account email (from the JSON) as **Editor**

### 3. Gmail API credentials

1. In Google Cloud Console, enable **Gmail API**
2. Create **OAuth 2.0 Client ID** (Desktop app) → Download JSON → save as `gmail_credentials.json` in this folder
3. First run: `python -m gmail` (opens browser for authorization, creates `gmail_token.json`)

### 4. Gemini API key (free)

Get your key from [Google AI Studio](https://aistudio.google.com)

### 5. Set environment variables (or edit config.py)

```bash
export GEMINI_API_KEY="your-gemini-key"
export GOOGLE_CREDENTIALS_FILE="credentials.json"
export GMAIL_CREDENTIALS_FILE="gmail_credentials.json"
export GOOGLE_SHEET_NAME="Job Tracker"
```

---

## Usage

```bash
# Check Gmail for job updates (manual)
python agent.py check-emails

# Add a job manually
python agent.py add

# Scrape job listings
python agent.py scrape

# List all applications
python agent.py list

# Filter by status
python agent.py list --status Interviewing

# Update a job's status/notes
python agent.py update

# See today's follow-up reminders
python agent.py followup

# Run daily scheduler (12:00 PM PKT)
python scheduler.py
```

---

## Google Sheet Layout

The agent auto-creates a worksheet called **"Applications"** with these columns:

| Column | Description |
|---|---|
| Company | Company name |
| Role | Job title |
| Url | Job posting link |
| Location | City or Remote |
| Salary | Salary info if available |
| Skills Required | AI-extracted skills list |
| Status | Applied / Interview Scheduled / Interview Completed / Interviewing / Offered / Rejected / Ghosted |
| Date Applied | YYYY-MM-DD |
| Last Follow Up | Date of last follow-up |
| Next Follow Up | Scheduled follow-up date |
| Notes | Any free-form notes |
| Email Thread ID | Gmail thread ID for auto-matching |

---

## Status Flow

```
Saved → Applied → Interview Scheduled → Interview Completed → Interviewing → Offered
                                                              ↘ Rejected
                                                              ↘ Ghosted
```

---

## Notes

- LinkedIn and Indeed actively block scrapers. If scraping fails, use `url` mode and paste a direct job posting link.
- Rozee.pk works best for Pakistan-based roles.
- The AI parser uses `gemini-1.5-flash` (free tier, 15 RPM).
- Duplicate URLs are skipped automatically when bulk-adding from scrape results.
- Gmail query targets unread emails with job-related subjects/senders.
- First Gmail run requires browser authorization.