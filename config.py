"""
config.py — Configuration & credentials
Copy this file and fill in your values.
"""

import os

# ─────────────────────────────────────────────
# Google Sheets
# ─────────────────────────────────────────────

# Path to your Google Service Account JSON key file
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

# The name (or ID) of your Google Sheet
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Job Tracker")

# Worksheet tab name inside the spreadsheet
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "Applications")

# ─────────────────────────────────────────────
# Google Gmail API (for reading unread emails)
# ─────────────────────────────────────────────

# Path to Gmail OAuth credentials (client_secret.json from Google Cloud)
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "gmail_credentials.json")

# Path to store Gmail OAuth token
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "gmail_token.json")

# Gmail query to find job update emails (unread by default)
GMAIL_QUERY = os.getenv(
    "GMAIL_QUERY",
    "is:unread (subject:interview OR subject:offer OR subject:rejection "
    'OR subject:"application status" OR subject:"next steps" '
    "OR from:recruiter OR from:hr OR from:talent OR from:hiring "
    "OR from:careers OR from:jobs)",
)

# ─────────────────────────────────────────────
# AI Model (free options: Gemini, Ollama)
# ─────────────────────────────────────────────

# AI Provider: "gemini" (Google), "ollama" (local), "anthropic" (paid)
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")

# Google Gemini API Key (free tier available at aistudio.google.com)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Google Gemini Model (free tier: gemini-1.5-flash)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Ollama settings (for local models like llama3, mistral, etc.)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# Anthropic API Key (legacy, paid)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ─────────────────────────────────────────────
# Application status options
# ─────────────────────────────────────────────

STATUS_OPTIONS = [
    "Saved",
    "Applied",
    "Interview Scheduled",
    "Interview Completed",
    "Interviewing",
    "Offered",
    "Rejected",
    "Ghosted",
]

# ─────────────────────────────────────────────
# Google Sheet column headers
# (order matters — matches the sheet layout)
# ─────────────────────────────────────────────

SHEET_COLUMNS = [
    "company",
    "role",
    "url",
    "location",
    "salary",
    "skills_required",
    "status",
    "date_applied",
    "last_follow_up",
    "next_follow_up",
    "notes",
    "email_thread_id",
]
