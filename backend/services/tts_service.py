import asyncio
from sarvamai import AsyncSarvamAI
import os
import base64
from dotenv import load_dotenv

load_dotenv()

class TTSService:
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        self._cache = {}
        if self.api_key:
            self.client = AsyncSarvamAI(api_subscription_key=self.api_key)
            print("TTS: Initialized with Sarvam AI client")
        else:
            self.client = None
            print("TTS: Running in MOCK mode (no API key found)")

    async def get_cached_or_synthesize(self, text: str, lang: str = "hi-IN") -> bytes | None:
        cache_key = f"{lang}:{text.strip()}"
        if cache_key in self._cache:
            print("TTS: Served from memory cache (Zero Latency)!")
            return self._cache[cache_key]
        
        audio = await self.synthesize(text, lang)
        if audio:
            self._cache[cache_key] = audio
        return audio

    async def synthesize(self, text: str, lang: str = "hi-IN") -> bytes | None:
        """
        Convert text to speech audio bytes (WAV).
        Returns the raw audio bytes or None on error.
        """
        if not self.client:
            print(f"TTS: Mocking audio for: {text[:50]}...")
            # Return a minimal valid WAV (silence) for mock testing
            return self._mock_wav()

        try:
            response = await self.client.text_to_speech.convert(
                text=text,
                target_language_code=lang,
                speaker="anushka",
                model="bulbul:v2"
            )
            
            # Response contains base64 encoded audio
            if hasattr(response, 'audios') and response.audios:
                audio_b64 = response.audios[0]
                audio_bytes = base64.b64decode(audio_b64)
                print(f"TTS: Generated {len(audio_bytes)} bytes for: {text[:40]}...")
                return audio_bytes
            elif hasattr(response, 'audio_base64'):
                audio_bytes = base64.b64decode(response.audio_base64)
                print(f"TTS: Generated {len(audio_bytes)} bytes for: {text[:40]}...")
                return audio_bytes
            else:
                print(f"TTS: Unexpected response format: {dir(response)}")
                return None
                
        except Exception as e:
            print(f"TTS Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _mock_wav(self) -> bytes:
        """Generate a short silent WAV for mock mode."""
        import struct
        import io
        
        sample_rate = 16000
        duration = 0.5  # 0.5 seconds of silence
        num_samples = int(sample_rate * duration)
        
        wav = io.BytesIO()
        wav.write(b'RIFF')
        data_size = num_samples * 2  # 16-bit samples
        wav.write(struct.pack('<I', 36 + data_size))
        wav.write(b'WAVE')
        wav.write(b'fmt ')
        wav.write(struct.pack('<I', 16))
        wav.write(struct.pack('<H', 1))  # PCM
        wav.write(struct.pack('<H', 1))  # Mono
        wav.write(struct.pack('<I', sample_rate))
        wav.write(struct.pack('<I', sample_rate * 2))
        wav.write(struct.pack('<H', 2))
        wav.write(struct.pack('<H', 16))
        wav.write(b'data')
        wav.write(struct.pack('<I', data_size))
        wav.write(b'\x00' * data_size)
        
        return wav.getvalue()


tts_service = TTSService()
