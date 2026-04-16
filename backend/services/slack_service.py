import os
from slack_sdk import WebClient
from dotenv import load_dotenv

load_dotenv()

class SlackService:
    def __init__(self):
        self.token = os.getenv("SLACK_TOKEN")
        self.client = None
        if self.token:
            self.client = WebClient(token=self.token)
            print("SLACK: Initialized with token")
        else:
            print("SLACK: Missing SLACK_TOKEN in .env")

    def send_message(self, channel, text):
        if not self.client:
            return "Error: Slack token missing."
        try:
            # Note: channel can be a name like '#general' (if the bot is in it) or ID
            self.client.chat_postMessage(channel=channel, text=text)
            return f"Message sent to Slack channel '{channel}'."
        except Exception as e:
            return f"Error sending to Slack: {str(e)}"

    def read_latest_messages(self, channel, limit=3):
        if not self.client:
            return "Error: Slack token missing."
        try:
            # First need to find channel ID from name if it's a name
            channel_id = channel
            if channel.startswith('#'):
                results = self.client.conversations_list()
                for c in results['channels']:
                    if c['name'] == channel[1:]:
                        channel_id = c['id']
                        break
            
            result = self.client.conversations_history(channel=channel_id, limit=limit)
            messages = result.get('messages', [])
            if not messages:
                return f"No messages found in {channel}."
            
            output = f"Latest messages in {channel}:\n"
            for m in messages:
                user = m.get('user', 'system')
                text = m.get('text', '')
                output += f"- User {user}: {text}\n"
            return output
        except Exception as e:
            return f"Error reading Slack: {str(e)}"

slack_service = SlackService()
