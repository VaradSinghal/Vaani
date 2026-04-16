import asyncio
import json
import re
import io
import struct
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from services.asr_service import asr_service
from services.tts_service import tts_service
from services.llm_service import llm_service
import sys
import codecs
from dotenv import load_dotenv

# Fix Windows console encoding for UTF-8
if sys.platform == "win32":
    try:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    except Exception:
        pass # Fallback if already detached

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TitleRequest(BaseModel):
    message: str

@app.post("/api/generate-title")
async def generate_title_endpoint(req: TitleRequest):
    title = await llm_service.generate_title(req.message)
    return {"title": title}


def pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 16000, channels: int = 1, sample_width: int = 2) -> bytes:
    """Convert raw PCM Int16 bytes to a valid WAV file."""
    wav_buffer = io.BytesIO()
    data_size = len(pcm_bytes)
    # WAV header
    wav_buffer.write(b'RIFF')
    wav_buffer.write(struct.pack('<I', 36 + data_size))  # File size - 8
    wav_buffer.write(b'WAVE')
    wav_buffer.write(b'fmt ')
    wav_buffer.write(struct.pack('<I', 16))  # Chunk size
    wav_buffer.write(struct.pack('<H', 1))   # PCM format
    wav_buffer.write(struct.pack('<H', channels))
    wav_buffer.write(struct.pack('<I', sample_rate))
    wav_buffer.write(struct.pack('<I', sample_rate * channels * sample_width))  # Byte rate
    wav_buffer.write(struct.pack('<H', channels * sample_width))  # Block align
    wav_buffer.write(struct.pack('<H', sample_width * 8))  # Bits per sample
    wav_buffer.write(b'data')
    wav_buffer.write(struct.pack('<I', data_size))
    wav_buffer.write(pcm_bytes)
    return wav_buffer.getvalue()


# Utility to split streaming text into sentences for TTS
async def sentence_stream(token_generator):
    buffer = ""
    # Punctuation marks for various languages including Indian (।, ., ?, !)
    sentence_endings = r"[।\.\?\!]"
    
    async for token in token_generator:
        buffer += token
        # Check if we have a full sentence
        parts = re.split(f"({sentence_endings})", buffer)
        
        # If we have at least one ending mark
        if len(parts) > 1:
            # Reconstruct sentences except the last part (which might be incomplete)
            for i in range(0, len(parts) - 1, 2):
                sentence = parts[i] + parts[i+1]
                if sentence.strip():
                    yield sentence.strip()
            buffer = parts[-1]
    
    # Yield remaining text if any
    if buffer.strip():
        yield buffer.strip()


@app.websocket("/voice-agent")
async def voice_agent_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WS: Client connected")

    try:
        while True:
            # Wait for audio recording session
            audio_chunks: list[bytes] = []
            
            while True:
                data = await websocket.receive()
                
                if "bytes" in data:
                    audio_chunks.append(data["bytes"])
                elif "text" in data:
                    msg = json.loads(data["text"])
                    if msg.get("type") == "eos":
                        break
                    elif msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                        continue

            if not audio_chunks:
                continue
            
            # Combine all audio chunks into a single PCM buffer
            full_pcm = b"".join(audio_chunks)
            print(f"WS: Received {len(full_pcm)} bytes of audio ({len(audio_chunks)} chunks)")
            
            # Convert PCM to WAV for ASR
            wav_data = pcm_to_wav(full_pcm)
            
            # Step 1: ASR - Transcribe the audio
            await websocket.send_json({"type": "status", "status": "processing"})
            transcript, language = await asr_service.transcribe(wav_data)
            
            if not transcript or not transcript.strip():
                print("WS: Empty transcript, skipping")
                await websocket.send_json({"type": "status", "status": "idle"})
                continue
            
            print(f"WS: Transcript ({language}): {transcript}")
            
            # Send transcript to frontend
            await websocket.send_json({
                "type": "transcript",
                "text": transcript,
                "is_final": True,
                "language": language
            })
            
            # Step 2: LLM - Generate response
            await websocket.send_json({"type": "status", "status": "thinking"})
            
            llm_gen = llm_service.stream_chat(transcript)
            
            # Step 3: Pipe LLM -> Sentence Buffer -> TTS -> Client
            await websocket.send_json({"type": "status", "status": "speaking"})
            
            async for sentence in sentence_stream(llm_gen):
                print(f"WS: LLM sentence: {sentence}")
                
                # Send agent text to frontend
                await websocket.send_json({
                    "type": "agent_transcript",
                    "text": sentence
                })
                
                # TTS - Convert sentence to speech and send
                audio_bytes = await tts_service.synthesize(sentence, language)
                if audio_bytes:
                    await websocket.send_bytes(audio_bytes)
            
            # Signal response complete
            await websocket.send_json({"type": "response_end"})
            print("WS: Response complete")

    except WebSocketDisconnect:
        print("WS: Client disconnected")
    except Exception as e:
        print(f"WS: Error - {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("WS: Connection closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, ws="wsproto")
