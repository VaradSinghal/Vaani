import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

class NotionService:
    def __init__(self):
        self.api_key = os.getenv("NOTION_API_KEY")
        self.page_id = os.getenv("NOTION_PAGE_ID") # The target page to append notes to
        self.client = None
        if self.api_key:
            self.client = Client(auth=self.api_key)
            print("NOTION: Initialized with API key")
        else:
            print("NOTION: Missing NOTION_API_KEY in .env")

    def append_voice_note(self, text):
        if not self.client:
            return "Error: Notion API key missing."
        if not self.page_id:
            return "Error: target Notion Page ID missing in .env."

        try:
            self.client.blocks.children.append(
                block_id=self.page_id,
                children=[
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": text
                                    }
                                }
                            ]
                        }
                    }
                ]
            )
            return "Note appended to Notion successfully."
        except Exception as e:
            return f"Error appending to Notion: {str(e)}"

notion_service = NotionService()
