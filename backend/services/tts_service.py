import asyncio
from sarvamai import AsyncSarvamAI
import os
import base64
from dotenv import load_dotenv

load_dotenv()

class TTSService:
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        if self.api_key:
            self.client = AsyncSarvamAI(api_subscription_key=self.api_key)
            print("TTS: Initialized with Sarvam AI client")
        else:
            self.client = None
            print("TTS: Running in MOCK mode (no API key found)")

    async def stream_tts(self, text: str, lang: str = "hi-IN"):
        if not self.client:
            print(f"TTS: Mocking audio for text: {text}")
            yield b"MOCK_AUDIO_CHUNK"
            return

        try:
            async with self.client.text_to_speech_streaming.connect(
                model="bulbul:v3",
                send_completion_event=True
            ) as ws:
                # Configuration must be the first message
                await ws.configure(
                    target_language_code=lang, 
                    speaker="shubh",
                    speech_sample_rate=16000,
                    min_buffer_size=50,
                    max_chunk_length=200
                )
                
                await ws.convert(text=text)
                await ws.flush()
                
                async for message in ws:
                    # Based on documentation: message can be AudioOutput or EventResponse
                    if hasattr(message, 'data') and hasattr(message.data, 'audio'):
                        # Documentation shows audio is base64 in data.audio
                        audio_chunk = base64.b64decode(message.data.audio)
                        yield audio_chunk
                    elif hasattr(message, 'data') and hasattr(message.data, 'event_type'):
                        if message.data.event_type == "final":
                            break
        except Exception as e:
            print(f"TTS Streaming Error: {e}")

tts_service = TTSService()
