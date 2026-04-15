import asyncio
import io
from sarvamai import AsyncSarvamAI
import os
from dotenv import load_dotenv

load_dotenv()

class ASRService:
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        if self.api_key:
            self.client = AsyncSarvamAI(api_subscription_key=self.api_key)
            print("ASR: Initialized with Sarvam AI client")
        else:
            self.client = None
            print("ASR: Running in MOCK mode (no API key found)")

    async def transcribe(self, wav_bytes: bytes) -> tuple[str, str]:
        """
        Transcribe WAV audio bytes to text.
        Returns (transcript, language_code).
        """
        if not self.client:
            print("ASR: Mocking transcription...")
            await asyncio.sleep(0.3)
            return ("नमस्ते, मैं ठीक हूँ", "hi-IN")

        try:
            # Create a file-like object from the WAV bytes
            audio_file = io.BytesIO(wav_bytes)
            audio_file.name = "audio.wav"

            response = await self.client.speech_to_text.transcribe(
                file=audio_file,
                model="saaras:v3",
                mode="transcribe"
            )
            
            transcript = response.transcript if hasattr(response, 'transcript') else str(response)
            language = getattr(response, 'language_code', 'hi-IN')
            
            print(f"ASR: Transcribed -> '{transcript}' (lang: {language})")
            return (transcript, language)
            
        except Exception as e:
            print(f"ASR Error: {e}")
            import traceback
            traceback.print_exc()
            return ("", "hi-IN")


asr_service = ASRService()
