import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Requesting universal workspace scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'  
]

def get_google_credentials(interactive=True):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("GOOGLE AUTH: Token expired, refreshing...")
                creds.refresh(Request())
            except Exception as e:
                print(f"GOOGLE AUTH: Refresh failed ({e}), falling back to interactive login.")
                creds = None
        
        if (not creds or not creds.valid) and interactive:
            print("GOOGLE AUTH: No valid token, starting interactive login...")
            if not os.path.exists('credentials.json'):
                print("GOOGLE AUTH: Missing credentials.json")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        else:
            print("GOOGLE AUTH: Authentication required but in non-interactive mode. Please restart server.")
            return None
            
    return creds
