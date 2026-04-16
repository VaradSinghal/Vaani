import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from utils.google_auth import get_google_credentials

class GmailService:
    def __init__(self):
        self.creds = None
        self.service = None

    def _authenticate(self):
        if self.service:
            return True
        try:
            self.creds = get_google_credentials(interactive=False)
            if not self.creds: return False
            self.service = build('gmail', 'v1', credentials=self.creds)
            print("GMAIL: Authenticated successfully")
            return True
        except Exception as e:
            print(f"GMAIL INIT ERROR: {e}")
            return False

    def get_unread_emails(self, max_results=3):
        if not self._authenticate(): return "Error: Gmail API not authenticated."
        try:
            results = self.service.users().messages().list(userId='me', q='is:unread', maxResults=max_results).execute()
            messages = results.get('messages', [])
            if not messages:
                return "No unread emails."
            
            output = "Top unread emails:\n"
            for msg in messages:
                m = self.service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['Subject', 'From']).execute()
                headers = m.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                output += f"- From: {sender} | Subject: {subject}\n"
            return output
        except Exception as e:
            return f"Error fetching emails: {str(e)}"

    def send_email(self, to, subject, body):
        if not self._authenticate(): return "Error: Gmail API not authenticated."
        try:
            message = EmailMessage()
            message.set_content(body)
            message['To'] = to
            message['From'] = 'me'
            message['Subject'] = subject

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {'raw': encoded_message}
            self.service.users().messages().send(userId='me', body=create_message).execute()
            return f"Email sent to {to} successfully."
        except Exception as e:
            return f"Error sending email: {str(e)}"

gmail_service = GmailService()
