import asyncio
from sarvamai import AsyncSarvamAI
import os
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        if self.api_key:
            self.client = AsyncSarvamAI(api_subscription_key=self.api_key)
            print("LLM: Initialized with Sarvam AI client")
        else:
            self.client = None
            print("LLM: Running in MOCK mode (no API key found)")

    async def stream_chat(self, user_input: str, system_prompt: str = None):
        if not self.client:
            # Mock behavior
            print("LLM: Mocking response...")
            yield "नमस्ते! मैं आपकी क्या सहायता कर सकता हूँ?"
            return

        if not system_prompt:
            system_prompt = (
                "You are 'Vaani', a helpful and concise multilingual voice assistant. "
                "Respond in the same language as the user's input. "
                "Keep responses extremely short and conversational (max 1-2 sentences). "
                "Avoid using special characters or markdown formatting as your response will be read by a TTS engine."
            )

        try:
            stream = await self.client.chat.completions(
                model="sarvam-105b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                stream=True
            )
            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
        except Exception as e:
            print(f"LLM Streaming Error: {e}")

    async def generate_title(self, user_input: str) -> str:
        if not self.client:
            return "Mock Session"
            
        system_prompt = (
            "Generate a very short, concise title (max 4 words) summarizing the following user message. "
            "Do not include quotes or any extra text, just the topic."
        )
        title = ""
        try:
            stream = await self.client.chat.completions(
                model="sarvam-105b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3,
                stream=True
            )
            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        title += delta.content
            return title.strip('"\' \n').title()[:50]
        except Exception as e:
            print(f"LLM Title Gen Error: {e}")
            return "New Chat"

llm_service = LLMService()
