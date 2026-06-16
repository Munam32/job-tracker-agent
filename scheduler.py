"""
scheduler.py — Background scheduler for daily Gmail checks at 12:00 PM PKT (Asia/Karachi)
Uses APScheduler with timezone support.
"""

import os
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import AI_PROVIDER, GEMINI_API_KEY
from gmail import GmailClient, parse_email_status
from sheets import SheetsClient
from ai_parser import AIParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PKT_TIMEZONE = pytz.timezone('Asia/Karachi')


class JobTrackerScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=PKT_TIMEZONE)
        self.gmail_client = GmailClient()
        self.sheets_client = SheetsClient()
        self.ai_parser = AIParser()

    def check_emails_and_update(self):
        """Main job: fetch unread emails, parse status, update Google Sheets."""
        logger.info(f"[{datetime.now(PKT_TIMEZONE)}] Starting daily email check...")
        
        try:
            emails = self.gmail_client.fetch_unread_job_emails()
            logger.info(f"Found {len(emails)} unread job-related emails")
            
            all_apps = self.sheets_client.get_all_records()
            
            for email in emails:
                parsed = parse_email_status(email, self.ai_parser)
                if not parsed:
                    logger.info(f"Email {email['id']} not recognized as job-related, skipping")
                    continue
                
                logger.info(f"Parsed: {parsed['company']} - {parsed['role']} - {parsed['status']} (confidence: {parsed['confidence']})")
                
                match = self._find_matching_application(all_apps, parsed)
                if match:
                    row_idx = match['_row_index']
                    self._update_application_status(row_idx, parsed, email)
                else:
                    logger.info(f"No matching application found for {parsed['company']} - {parsed['role']}, creating new entry")
                    self._create_new_application(parsed, email)
                
                self.gmail_client.mark_as_read(email['id'])
                
        except Exception as e:
            logger.error(f"Error in daily email check: {e}")

    def _find_matching_application(self, applications: list, parsed: dict) -> Optional[dict]:
        """Find existing application by company, role, or email thread ID."""
        for i, app in enumerate(applications):
            app_with_idx = {**app, '_row_index': i + 2}  # +2 for header row and 1-indexing
            
            if parsed.get('email_thread_id') and app.get('email_thread_id') == parsed['email_thread_id']:
                return app_with_idx
            
            company_match = app.get('company', '').lower() == parsed['company'].lower()
            role_match = app.get('role', '').lower() == parsed['role'].lower()
            
            if company_match and role_match:
                return app_with_idx
                
            if company_match and parsed['role'].lower() in app.get('role', '').lower():
                return app_with_idx
        
        return None

    def _update_application_status(self, row_idx: int, parsed: dict, email: dict):
        """Update existing application with new status from email."""
        updates = {
            'status': parsed['status'],
            'notes': f"{parsed['notes']}\n\n[Auto-updated from email: {email['subject']} ({email['date']})]",
            'email_thread_id': parsed['email_thread_id'],
        }
        
        if parsed['status'] in ['Interview Scheduled', 'Interview Completed']:
            updates['next_follow_up'] = ''
        
        self.sheets_client.update_row(row_idx, updates)
        logger.info(f"Updated row {row_idx}: {parsed['company']} - {parsed['role']} -> {parsed['status']}")

    def _create_new_application(self, parsed: dict, email: dict):
        """Create new application entry from email."""
        new_row = {
            'company': parsed['company'],
            'role': parsed['role'],
            'url': '',
            'location': '',
            'salary': '',
            'skills_required': '',
            'status': parsed['status'],
            'date_applied': datetime.now(PKT_TIMEZONE).strftime('%Y-%m-%d'),
            'last_follow_up': '',
            'next_follow_up': '',
            'notes': f"[Auto-created from email: {email['subject']} ({email['date']})]\n{parsed['notes']}",
            'email_thread_id': parsed['email_thread_id'],
        }
        
        self.sheets_client.append_row(new_row)
        logger.info(f"Created new application: {parsed['company']} - {parsed['role']}")

    def start(self):
        """Start the scheduler with daily 12:00 PM PKT job."""
        trigger = CronTrigger(
            hour=12,
            minute=0,
            timezone=PKT_TIMEZONE
        )
        
        self.scheduler.add_job(
            self.check_emails_and_update,
            trigger=trigger,
            id='daily_email_check',
            name='Daily Gmail check for job updates',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler started. Daily email check at 12:00 PM PKT (Asia/Karachi)")
        
        try:
            import time
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    def run_once(self):
        """Run the email check once (for manual/testing)."""
        self.check_emails_and_update()


def main():
    """Entry point for running scheduler as a standalone script."""
    if not GEMINI_API_KEY and AI_PROVIDER == "gemini":
        print("ERROR: GEMINI_API_KEY not set in config.py or environment")
        return
    
    scheduler = JobTrackerScheduler()
    scheduler.start()


if __name__ == "__main__":
    main()