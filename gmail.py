import os
import json
import base64
from datetime import datetime
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import (
    GMAIL_CREDENTIALS_FILE,
    GMAIL_TOKEN_FILE,
    GMAIL_QUERY,
)


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailClient:
    def __init__(self):
        self.service = None
        self._authenticate()

    def _authenticate(self):
        creds = None
        if os.path.exists(GMAIL_TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(GMAIL_CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"Gmail credentials file not found at {GMAIL_CREDENTIALS_FILE}. "
                        "Please download from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    GMAIL_CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(GMAIL_TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        self.service = build('gmail', 'v1', credentials=creds)

    def fetch_unread_job_emails(self, max_results: int = 50) -> List[Dict]:
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=GMAIL_QUERY,
                maxResults=max_results
            ).execute()
            messages = results.get('messages', [])
            emails = []
            for msg in messages:
                email_data = self._get_email_details(msg['id'])
                if email_data:
                    emails.append(email_data)
            return emails
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def _get_email_details(self, message_id: str) -> Optional[Dict]:
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')

            body = self._extract_body(message['payload'])

            return {
                'id': message_id,
                'thread_id': message.get('threadId', ''),
                'subject': subject,
                'sender': sender,
                'date': date_str,
                'body': body,
                'snippet': message.get('snippet', '')
            }
        except HttpError as error:
            print(f"Error fetching email {message_id}: {error}")
            return None

    def _extract_body(self, payload: Dict) -> str:
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html':
                    data = part['body'].get('data', '')
                    if data and not body:
                        body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif 'parts' in part:
                    body += self._extract_body(part)
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif payload['mimeType'] == 'text/html':
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        return body

    def mark_as_read(self, message_id: str):
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except HttpError as error:
            print(f"Error marking email as read: {error}")


def authorize_gmail():
    """Run the Gmail OAuth authorization flow manually.

    Creates gmail_token.json if it doesn't exist or is expired.
    Safe to run multiple times — skips if token is already valid.
    """
    if not os.path.exists(GMAIL_CREDENTIALS_FILE):
        print(
            f"ERROR: Credentials file not found: {GMAIL_CREDENTIALS_FILE}\n"
            "Download OAuth 2.0 Client ID (Desktop app) JSON from\n"
            "  https://console.cloud.google.com/apis/credentials\n"
            f"and save it as '{GMAIL_CREDENTIALS_FILE}' in the project root.",
            flush=True,
        )
        return

    if os.path.exists(GMAIL_TOKEN_FILE):
        print(f"Token file '{GMAIL_TOKEN_FILE}' already exists. Checking validity...", flush=True)

    client = GmailClient()
    print(f"Gmail authorization OK. Token: {GMAIL_TOKEN_FILE}", flush=True)


def parse_email_status(email: Dict, ai_parser) -> Optional[Dict]:
    prompt = f"""
    Analyze this job application email and extract the following information as JSON:
    
    Subject: {email['subject']}
    From: {email['sender']}
    Date: {email['date']}
    Body: {email['body'][:3000]}
    
    Return JSON with these fields:
    - company: Company name (string)
    - role: Job role/title (string)
    - status: One of ["Applied", "Under Review", "Interview Scheduled", "Interview Completed", "Offer Received", "Rejected", "Withdrawn"]
    - confidence: Confidence score 0-1 (float)
    - notes: Any relevant details (string)
    
    If this is NOT a job application related email, return null.
    """
    try:
        result = ai_parser.parse_with_ai(prompt)
        if result and result.get('company') and result.get('role'):
            return {
                'company': result['company'],
                'role': result['role'],
                'status': result.get('status', 'Applied'),
                'confidence': result.get('confidence', 0.5),
                'notes': result.get('notes', ''),
                'email_thread_id': email['thread_id'],
                'email_date': email['date']
            }
    except Exception as e:
        print(f"Error parsing email with AI: {e}")
    return None


if __name__ == "__main__":
    authorize_gmail()