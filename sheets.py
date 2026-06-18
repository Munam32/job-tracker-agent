"""
sheets.py — Google Sheets integration via gspread
"""

import gspread
from google.oauth2.service_account import Credentials
from typing import Optional

from config import (
    GOOGLE_CREDENTIALS_FILE,
    GOOGLE_SHEET_NAME,
    WORKSHEET_NAME,
    SHEET_COLUMNS,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class SheetsClient:
    def __init__(self):
        creds = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_FILE, scopes=SCOPES
        )
        self.gc   = gspread.authorize(creds)
        self.sh   = self.gc.open(GOOGLE_SHEET_NAME)
        self.ws   = self._get_or_create_worksheet()

    # ──────────────────────────────────────────
    # Setup
    # ──────────────────────────────────────────

    def _get_or_create_worksheet(self) -> gspread.Worksheet:
        """Return the worksheet, creating it with headers if it doesn't exist."""
        try:
            ws = self.sh.worksheet(WORKSHEET_NAME)
            # Ensure headers row exists
            if ws.row_count == 0 or not ws.row_values(1):
                ws.append_row(self._headers(), value_input_option="RAW")
        except gspread.WorksheetNotFound:
            ws = self.sh.add_worksheet(
                title=WORKSHEET_NAME, rows=1000, cols=len(SHEET_COLUMNS)
            )
            ws.append_row(self._headers(), value_input_option="RAW")
            # Bold the header row
            ws.format("1:1", {"textFormat": {"bold": True}})
        return ws

    def _headers(self) -> list[str]:
        return [col.replace("_", " ").title() for col in SHEET_COLUMNS]

    # ──────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────

    def get_all_jobs(self) -> list[dict]:
        """Return all rows as a list of dicts, with a _row key for updates."""
        records = self.ws.get_all_records(expected_headers=self._headers())
        jobs = []
        for i, rec in enumerate(records, start=2):   # row 1 = headers
            job = {col: rec.get(col.replace("_", " ").title(), "") for col in SHEET_COLUMNS}
            job["_row"] = i
            jobs.append(job)
        return jobs

    def _url_exists(self, url: str) -> bool:
        """Check if a job URL is already tracked (prevents duplicates)."""
        if not url:
            return False
        try:
            cell = self.ws.find(url)
            return cell is not None
        except gspread.exceptions.CellNotFound:
            return False

    # ──────────────────────────────────────────
    # Write
    # ──────────────────────────────────────────

    def add_job(self, job: dict) -> bool:
        """Append a single job row. Returns True if added, False if duplicate."""
        url = (job.get("url") or "").strip()
        if url and self._url_exists(url):
            return False

        company = (job.get("company") or "").strip().lower()
        role    = (job.get("role") or "").strip().lower()
        if company and role:
            for j in self.get_all_jobs():
                if (
                    (j.get("company") or "").strip().lower() == company
                    and (j.get("role") or "").strip().lower() == role
                ):
                    return False

        row = [job.get(col, "") for col in SHEET_COLUMNS]
        self.ws.append_row(row, value_input_option="USER_ENTERED")
        return True

    def bulk_add_jobs(self, jobs: list[dict]) -> int:
        """
        Append multiple jobs, skipping duplicates by URL.
        Returns the count of newly added jobs.
        """
        added = 0
        for job in jobs:
            if self._url_exists(job.get("url", "")):
                continue
            self.add_job(job)
            added += 1
        return added

    def update_job(
        self,
        row: int,
        status:         Optional[str] = None,
        notes:          Optional[str] = None,
        last_follow_up: Optional[str] = None,
        next_follow_up: Optional[str] = None,
    ) -> None:
        """Update specific fields of a row by its sheet row number."""
        col_map = {col: i + 1 for i, col in enumerate(SHEET_COLUMNS)}

        updates = {
            "status":         status,
            "notes":          notes,
            "last_follow_up": last_follow_up,
            "next_follow_up": next_follow_up,
        }

        batch = []
        for field, value in updates.items():
            if value is not None:
                col_letter = gspread.utils.rowcol_to_a1(row, col_map[field])
                batch.append({
                    "range": col_letter,
                    "values": [[value]],
                })

        if batch:
            self.ws.batch_update(batch, value_input_option="USER_ENTERED")

    def get_all_records(self) -> list[dict]:
        """Return all rows as a list of dicts (alias for get_all_jobs)."""
        return self.get_all_jobs()

    def update_row(self, row: int, updates: dict) -> None:
        """Update multiple fields of a row by its sheet row number."""
        col_map = {col: i + 1 for i, col in enumerate(SHEET_COLUMNS)}

        batch = []
        for field, value in updates.items():
            if value is not None and field in col_map:
                col_letter = gspread.utils.rowcol_to_a1(row, col_map[field])
                batch.append({
                    "range": col_letter,
                    "values": [[value]],
                })

        if batch:
            self.ws.batch_update(batch, value_input_option="USER_ENTERED")

    def delete_job(self, row: int) -> None:
        """Delete a row by its sheet row number (1-indexed)."""
        self.ws.delete_rows(row)

    def append_row(self, job: dict) -> None:
        """Append a single job row (alias for add_job)."""
        row = [job.get(col, "") for col in SHEET_COLUMNS]
        self.ws.append_row(row, value_input_option="USER_ENTERED")
