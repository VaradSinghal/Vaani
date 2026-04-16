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

@app.on_event("startup")
async def startup_event():
    # Pre-cache filler words for instant zero-latency playback
    from services.tts_service import tts_service
    print("Pre-caching zero-latency filler words...")
    await tts_service.get_cached_or_synthesize("एक मिनट, मैं चेक करती हूँ।", "hi-IN")
    await tts_service.get_cached_or_synthesize("एक मिनट, मैं चेक करती हूँ।", "en-IN")

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
    # Punctuation marks for various languages including Indian (।, ., ?, !), plus comma/colons for faster first-chunks
    sentence_endings = r"[।\.\?\!\,:\n]"
    
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
                
                if data["type"] == "websocket.disconnect":
                    raise WebSocketDisconnect(data.get("code", 1000))
                
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
            
            # Step 2: Edge Intent Routing vs LLM - Generate response
            await websocket.send_json({"type": "status", "status": "thinking"})
            
            transcript_lower = transcript.strip().lower()
            calendar_intents = [
                "check my calendar", "what's my schedule", "calendar", 
                "agenda", "events today", "meetings", "check my schedule", 
                "what do i have today", "mere meetings", "calendar check karo"
            ]
            
            is_fast_route = any(intent in transcript_lower for intent in calendar_intents)
            
            if is_fast_route:
                print("WS: ROUTER -> Fast-routing to Calendar Tool.")
                
                # Push zero-latency filler directly to frontend
                filler_phrase = "एक मिनट, मैं चेक करती हूँ।"
                await websocket.send_json({"type": "agent_transcript", "text": filler_phrase})
                audio_bytes = await tts_service.get_cached_or_synthesize(filler_phrase, language)
                if audio_bytes:
                    await websocket.send_bytes(audio_bytes)
                    
                # Execute tool directly in Python
                from services.calendar_service import calendar_service
                result = calendar_service.get_upcoming_events()
                
                # Generate final formatting via LLM
                fast_prompt = f"Summarize these events concisely for voice playback: {result}"
                llm_gen = llm_service.stream_chat(transcript, system_prompt=fast_prompt)
            else:
                llm_gen = llm_service.stream_chat(transcript)
            
            
            # Step 3: Pipe LLM -> Sentence Buffer -> TTS -> Client
            await websocket.send_json({"type": "status", "status": "speaking"})
            
            queue = asyncio.Queue()
            
            async def tts_worker():
                while True:
                    sentence = await queue.get()
                    if sentence is None:
                        break
                    
                    # TTS - Convert sentence to speech and send
                    audio_bytes = await tts_service.get_cached_or_synthesize(sentence, language)
                    if audio_bytes:
                        await websocket.send_bytes(audio_bytes)
                        
                    queue.task_done()
            
            # Start TTS worker concurrently
            tts_task = asyncio.create_task(tts_worker())
            
            # Feed sentences to the queue as fast as LLM produces them
            try:
                async for sentence in sentence_stream(llm_gen):
                    print(f"WS: LLM sentence: {sentence}")
                    # Send agent text to frontend as soon as we have it
                    await websocket.send_json({
                        "type": "agent_transcript",
                        "text": sentence
                    })
                    await queue.put(sentence)
            except Exception as e:
                print(f"WS: Error in LLM stream: {e}")
                
            # Wait for all audio to finish
            await queue.put(None)
            await tts_task
            
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
