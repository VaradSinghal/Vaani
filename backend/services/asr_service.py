import asyncio
from sarvamai import AsyncSarvamAI
import os
import base64
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

    async def stream_asr(self, audio_generator, callback):
        if not self.client:
            # Mock behavior for testing pipeline flow
            print("ASR: Mocking transcription...")
            await asyncio.sleep(1) # Simulate network delay
            await callback("नमस्ते", True, "hi-IN")
            return

        try:
            # Using documentation-recommended saaras:v3 and speech_to_text_streaming
            async with self.client.speech_to_text_streaming.connect(
                model="saaras:v3",
                mode="transcribe",
                language_code="hi-IN", # Default, can be tuned
                high_vad_sensitivity=True,
                vad_signals=True
            ) as ws:
                async def send_audio():
                    async for chunk in audio_generator:
                        if chunk is None:
                            break
                        # Sarvam SDK expects base64 encoded audio
                        audio_b64 = base64.b64encode(chunk).decode("utf-8")
                        await ws.transcribe(audio=audio_b64, encoding="audio/wav", sample_rate=16000)
                    await ws.flush()

                async def receive_transcripts():
                    async for msg in ws:
                        # msg type is SpeechToTextStreamingResponse
                        msg_type = getattr(msg, 'type', None)
                        
                        if msg_type == "speech_start":
                            print("ASR: Speech detected")
                        elif msg_type == "speech_end":
                            print("ASR: Speech ended")
                        elif msg_type == "transcript":
                            # msg.data is SpeechToTextTranscriptionData
                            transcript = msg.data.transcript
                            lang = getattr(msg.data, 'language_code', 'hi-IN')
                            # For saaras:v3, we'll assume transcripts are final enough to process 
                            # or check if there's a more specific finality flag in metrics/extra
                            await callback(transcript, True, lang)
                
                await asyncio.gather(send_audio(), receive_transcripts())
        except Exception as e:
            print(f"ASR Streaming Error: {e}")

asr_service = ASRService()
