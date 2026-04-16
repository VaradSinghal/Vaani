import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

class CalendarService:
    def __init__(self):
        self.creds = None
        self.service = None
        # We don't authenticate immediately on load because it might block server startup headless.
        # We will lazy-load authentication.

    def _authenticate(self):
        if self.service:
            return True
            
        try:
            if os.path.exists('token.json'):
                self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
                
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists('credentials.json'):
                        print("CALENDAR: Missing credentials.json")
                        return False
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    self.creds = flow.run_local_server(port=8080)
                with open('token.json', 'w') as token:
                    token.write(self.creds.to_json())
            
            self.service = build('calendar', 'v3', credentials=self.creds)
            print("CALENDAR: Authenticated successfully")
            return True
        except Exception as e:
            print(f"CALENDAR INIT ERROR: {e}")
            return False

    def get_upcoming_events(self, max_results=5):
        if not self._authenticate(): return "Error: Calendar API not authenticated locally."
        
        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId='primary', timeMin=now,
                maxResults=max_results, singleEvents=True,
                orderBy='startTime').execute()
            events = events_result.get('items', [])
            
            if not events:
                return "No upcoming events found on your calendar."
            
            output = "Upcoming events:\n"
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                summary = event.get('summary', 'Busy')
                output += f"- {start}: {summary}\n"
            return output
        except Exception as e:
            return f"Error fetching events: {str(e)}"

    def schedule_event(self, summary, start_time, end_time, description=""):
        if not self._authenticate(): return "Error: Calendar API not authenticated locally."
        try:
            event = {
              'summary': summary,
              'description': description,
              'start': {
                'dateTime': start_time,
                'timeZone': 'Asia/Kolkata',
              },
              'end': {
                'dateTime': end_time,
                'timeZone': 'Asia/Kolkata',
              },
            }
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            return f"Event created successfully. Details: {summary} from {start_time} to {end_time}."
        except Exception as e:
            return f"Error scheduling event: {str(e)}"

    def get_event_details(self, summary_query: str):
        if not self._authenticate(): return "Error: Calendar API not authenticated locally."
        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId='primary', q=summary_query, timeMin=now,
                maxResults=3, singleEvents=True, orderBy='startTime').execute()
            events = events_result.get('items', [])
            
            if not events:
                return f"No upcoming events found matching '{summary_query}'."
                
            output = f"Details for '{summary_query}':\n"
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                desc = event.get('description', 'No description')
                output += f"- Title: {event.get('summary')} | Start: {start} | End: {end} | Desc: {desc}\n"
            return output
        except Exception as e:
            return f"Error fetching details: {str(e)}"

    def cancel_event(self, summary_query: str):
        if not self._authenticate(): return "Error: Calendar API not authenticated locally."
        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId='primary', q=summary_query, timeMin=now,
                maxResults=1, singleEvents=True, orderBy='startTime').execute()
            events = events_result.get('items', [])
            
            if not events:
                return f"Could not find any upcoming event matching '{summary_query}' to cancel."
                
            event_id = events[0]['id']
            event_title = events[0].get('summary', 'Unknown Event')
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            return f"Successfully canceled the meeting: '{event_title}'"
        except Exception as e:
            return f"Error canceling event: {str(e)}"

calendar_service = CalendarService()
