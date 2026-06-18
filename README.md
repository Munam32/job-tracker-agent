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

### 3. Configure APIs

This project requires **three** Google APIs. Follow each section below in order.

---

#### 3a. Google Sheets API + Google Drive API

These two APIs work together — the system uses a **Service Account** to write data to a Google Sheet.

**Step 1 — Create a Google Cloud project**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top of the page → click **New Project**
3. Name it something like `Job Tracker` → click **Create**
4. Make sure the new project is selected in the dropdown

**Step 2 — Enable the APIs**
1. In the left sidebar, go to **APIs & Services** → **Library**
2. Search for **Google Sheets API** → click it → click **Enable**
3. Go back to the Library → search for **Google Drive API** → click it → click **Enable**

**Step 3 — Create a Service Account**
1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → select **Service Account**
3. Give it a name (e.g. `job-tracker-sa`) → click **Create and Continue**
4. Skip the optional role grants → click **Done**
5. In the **Service Accounts** list, click the email address of the one you just created
6. Go to the **Keys** tab → click **Add Key** → **Create New Key**
7. Choose **JSON** → click **Create** — a `.json` file will download automatically
8. Rename it to `credentials.json` and place it in the project root (`Job_Tracker/credentials.json`)

**Step 4 — Create and share the Google Sheet**
1. Go to [sheets.new](https://sheets.new) (or create via Google Drive)
2. Name the spreadsheet **"Job Tracker"** (must match `GOOGLE_SHEET_NAME` in config)
3. Copy the **Service Account email** — it looks like `job-tracker-sa@<project-id>.iam.gserviceaccount.com` (find it in the **Service Accounts** list in Google Cloud Console)
4. Click **Share** in the top-right of the sheet → paste the service account email → grant **Editor** access → click **Send**

> **Verify**: The sheet should appear empty; the system will auto-create the "Applications" worksheet with headers on first run.

---

#### 3b. Gmail API

This API uses **OAuth 2.0** (not a Service Account) to read your personal Gmail inbox.

**Step 1 — Enable the API**
1. In Google Cloud Console → **APIs & Services** → **Library**
2. Search for **Gmail API** → click it → click **Enable**

**Step 2 — Configure the OAuth consent screen**
1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type → click **Create**
3. Fill in:
   - **App name**: `Job Tracker`
   - **User support email**: your email
   - **Developer contact email**: your email
4. Click **Save and Continue**
5. **Scopes**: click **Add or Remove Scopes** → search for `Gmail API` → select `../auth/gmail.readonly` → click **Update** → **Save and Continue**
6. **Test users**: click **Add Users** → add your own Gmail address → **Save and Continue**
7. Review and click **Back to Dashboard**

**Step 3 — Create OAuth 2.0 credentials**
1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. For **Application type**, choose **Desktop app**
4. Name: `Job Tracker Desktop Client`
5. Click **Create**
6. A popup shows your Client ID and Secret — click **Download JSON**
7. Rename the file to `gmail_credentials.json` and place it in the project root (`Job_Tracker/gmail_credentials.json`)

**Step 4 — Authorize the application**
```bash
python -m gmail
```
This will open a browser window asking you to sign in to Google and grant read-only Gmail access. After authorizing, a `gmail_token.json` file is created automatically in the project root. You only need to do this once.

> **Troubleshooting**: If authorization fails, delete `gmail_token.json` and re-run `python -m gmail`. Make sure your Gmail address is added as a **Test user** in the OAuth consent screen.

---

#### 3c. Gemini API

The system uses Google's Gemini AI (free tier) to classify email content and extract job status.

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click **Get API Key** in the left sidebar
4. Click **Create API Key** → select your Google Cloud project (or create a new one)
5. Copy the API key

This only needs to be stored as an environment variable (next step) or in `config.py`. No credential files are needed.

---

### 4. Configure Environment Variables

The system reads configuration from environment variables. Choose your method:

**Option A — Linux / macOS (temporary, per session)**
```bash
export GEMINI_API_KEY="AIzaSy..."
export GOOGLE_CREDENTIALS_FILE="credentials.json"
export GMAIL_CREDENTIALS_FILE="gmail_credentials.json"
export GOOGLE_SHEET_NAME="Job Tracker"
```

**Option B — Windows PowerShell (temporary, per session)**
```powershell
$env:GEMINI_API_KEY="AIzaSy..."
$env:GOOGLE_CREDENTIALS_FILE="credentials.json"
$env:GMAIL_CREDENTIALS_FILE="gmail_credentials.json"
$env:GOOGLE_SHEET_NAME="Job Tracker"
```

**Option C — Windows (persistent via setx)**
```powershell
setx GEMINI_API_KEY "AIzaSy..."
setx GOOGLE_CREDENTIALS_FILE "credentials.json"
setx GMAIL_CREDENTIALS_FILE "gmail_credentials.json"
setx GOOGLE_SHEET_NAME "Job Tracker"
```

**Option D — Edit config.py directly** (not recommended for shared machines)
Open `config.py` and replace the empty values:
```python
GEMINI_API_KEY = "AIzaSy..."
GOOGLE_CREDENTIALS_FILE = "credentials.json"
GMAIL_CREDENTIALS_FILE = "gmail_credentials.json"
GOOGLE_SHEET_NAME = "Job Tracker"
```

> **Note**: Environment variables take precedence over `config.py` defaults. If you set both, the env var wins.

### 5. Run
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
