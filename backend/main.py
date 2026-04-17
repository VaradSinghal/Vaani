import os
# Force Offline Mode for ML Models to minimize latency and prevent network errors
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

import asyncio
import json
import re
import io
import struct
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Query
from services.asr_service import asr_service
from services.tts_service import tts_service
from services.llm_service import llm_service
from services.vector_store import vector_store
from services.memory_service import memory_service
from services.document_service import document_service
from services.agent_service import agent_service
import sys
import codecs
import base64
from typing import Optional, List
from pydantic import BaseModel
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
    # Load persisted vector store and initialize the embedding model (OFFLINE)
    print("Loading vector store and embedding model...")
    vector_store.load_from_disk()
    vector_store.initialize()
    print("Agent Studio: Initializing management routes...")
    print(f"Agent Studio: {len(agent_service.list_agents())} agents loaded.")
    
    # Pre-cache filler words for instant zero-latency playback
    from services.tts_service import tts_service
    from utils.google_auth import get_google_credentials
    print("Pre-caching zero-latency filler words...")
    await tts_service.get_cached_or_synthesize("एक मिनट, मैं चेक करती हूँ।", "hi-IN")
    await tts_service.get_cached_or_synthesize("एक मिनट, मैं चेक करती हूँ।", "en-IN")
    
    # print("Checking Google Workspace Authentication...")
    # This will open a browser window if token.json is missing/invalid
    # It runs at startup so it doesn't block the WebSocket loop later
    # get_google_credentials(interactive=True)

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


# ─── Document Upload & Management Endpoints ──────────────────────────

@app.post("/api/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    language: str = Form("en-IN"),
    user_id: str = Form("anonymous"),
):
    """Upload a document → parse → extract facts → vectorize."""
    file_bytes = await file.read()
    
    if len(file_bytes) > 10 * 1024 * 1024:  # 10MB limit
        return {"error": "File too large. Maximum 10MB."}
    
    result = await document_service.process_document(
        file_bytes=file_bytes,
        filename=file.filename,
        language=language,
    )
    return result


@app.get("/api/documents")
async def list_documents():
    """List all processed documents in the vector store."""
    docs = vector_store.get_documents()
    return {"documents": docs, "total_facts": vector_store.total_facts}


@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Remove a document and its facts from the vector store."""
    vector_store.remove_document(doc_id)
    vector_store.save_to_disk()
    return {"status": "deleted", "doc_id": doc_id}


@app.get("/api/search")
async def search_documents(q: str = Query(...), top_k: int = Query(5)):
    """Search document facts by semantic similarity."""
    results = vector_store.search(q, top_k=top_k)
    return {
        "query": q,
        "results": [
            {"text": r.text, "score": round(r.score, 3), "doc_title": r.doc_title, "doc_type": r.doc_type}
            for r in results
        ]
    }


# ─── Memory Endpoints ────────────────────────────────────────────────

@app.get("/api/memory/{user_id}")
async def get_user_memory(user_id: str):
    """View stored user facts."""
    facts = memory_service.get_user_facts(user_id)
    return {"user_id": user_id, "facts": facts, "count": len(facts)}


# ─── Agent Management Endpoints ──────────────────────────────────────

@app.get("/api/agents")
async def list_agents():
    """List all available custom agents."""
    return {"agents": agent_service.list_agents()}

class CreateAgentRequest(BaseModel):
    name: str
    description: str
    system_instructions: str
    role: str = "general"
    tools_enabled: Optional[List[str]] = None
    voice_id: str = "anushka"

class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_instructions: Optional[str] = None
    role: Optional[str] = None
    tools_enabled: Optional[List[str]] = None
    voice_id: Optional[str] = None

@app.post("/api/agents")
async def create_agent(req: CreateAgentRequest):
    """Create a new custom agent."""
    agent = agent_service.create_agent(
        name=req.name,
        description=req.description,
        system_instructions=req.system_instructions,
        role=req.role,
        tools_enabled=req.tools_enabled,
        voice_id=req.voice_id
    )
    return agent

@app.get("/api/voices")
async def get_voices():
    """List available vocal personas from Bulbul v2."""
    return [
        {"id": "anushka", "name": "Anushka", "gender": "Female", "style": "Clear, Professional"},
        {"id": "meera", "name": "Meera", "gender": "Female", "style": "Warm, Empathetic"},
        {"id": "pavithra", "name": "Pavithra", "gender": "Female", "style": "Formal, Informative"},
        {"id": "amrit", "name": "Amrit", "gender": "Male", "style": "Deep, Authoritative"},
        {"id": "vatsal", "name": "Vatsal", "gender": "Male", "style": "Friendly, Energetic"},
        {"id": "kumar", "name": "Kumar", "gender": "Male", "style": "Mature, Trustworthy"},
    ]

class PreviewVoiceRequest(BaseModel):
    voice_id: str
    text: str

@app.post("/api/voices/preview")
async def preview_voice(req: PreviewVoiceRequest):
    """Generate sample audio for UI auditioning."""
    audio = await tts_service.synthesize(req.text, speaker=req.voice_id)
    if not audio:
        return {"error": "Synthesis failed"}
    return {"audio": base64.b64encode(audio).decode("utf-8")}

@app.put("/api/agents/{agent_id}")
async def update_agent(agent_id: str, req: UpdateAgentRequest):
    """Update an existing custom agent."""
    updated = agent_service.update_agent(agent_id, req.dict(exclude_unset=True))
    if not updated:
        return {"error": "Agent not found"}
    return updated

@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete a custom agent."""
    success = agent_service.delete_agent(agent_id)
    return {"status": "success" if success else "not_found"}


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
    # More aggressive splitting: yield on commas, semicolons, and newlines for faster TTS startup
    sentence_endings = r"[।\.\?\!\,;\n]"
    max_words_before_yield = 12
    
    async for token in token_generator:
        if isinstance(token, dict):
            yield token
            continue
            
        buffer += str(token)
        
        # Check for word count to force a yield if the sentence is too long
        word_count = len(buffer.split())
        
        # Split on punctuation OR word count limit
        if re.search(sentence_endings, buffer) or word_count >= max_words_before_yield:
            parts = re.split(f"({sentence_endings})", buffer)
            
            if len(parts) > 1:
                # Standard punctuation split
                for i in range(0, len(parts) - 1, 2):
                    sentence = parts[i] + parts[i+1]
                    if sentence.strip():
                        yield sentence.strip()
                buffer = parts[-1]
            elif word_count >= max_words_before_yield:
                # Word count force yield
                yield buffer.strip()
                buffer = ""
    
    if buffer.strip():
        yield buffer.strip()


@app.websocket("/voice-agent")
async def voice_agent_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Generate unique session ID and extract user ID and Agent ID from query params
    session_id = str(uuid.uuid4())[:12]
    user_id = websocket.query_params.get("uid", "anonymous")
    agent_id = websocket.query_params.get("agent_id")
    
    # Resolve agent's voice
    speaker_id = "anushka"
    if agent_id:
        agent = agent_service.get_agent(agent_id)
        if agent:
            speaker_id = agent.get("voice_id", "anushka")
    
    print(f"WS: Client connected (session={session_id}, user={user_id[:8]}, agent={agent_id or 'default'}, voice={speaker_id})")

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
            
            # Step 2: Agent Response Generation
            await websocket.send_json({"type": "status", "status": "thinking"})
            
            # Use the unified Agent pipeline in LLM service with memory context
            queue = asyncio.Queue()
            
            llm_gen = llm_service.stream_chat(
                transcript,
                session_id=session_id,
                user_id=user_id,
                tts_queue=queue,
                agent_id=agent_id
            )
            
            
            # Step 3: Pipe LLM -> Sentence Buffer -> TTS -> Client
            await websocket.send_json({"type": "status", "status": "speaking"})
            
            async def tts_worker():
                while True:
                    sentence = await queue.get()
                    if sentence is None:
                        break
                    
                    # TTS - Convert sentence to speech and send
                    audio_bytes = await tts_service.synthesize(sentence, speaker=speaker_id)
                    if audio_bytes:
                        await websocket.send_bytes(audio_bytes)
                        
                    queue.task_done()
            
            # Start TTS worker concurrently
            tts_task = asyncio.create_task(tts_worker())
            
            # Feed sentences to the queue as fast as LLM produces them
            try:
                async for item in sentence_stream(llm_gen):
                    if isinstance(item, dict):
                        # Handle metadata like attribution or status
                        if item.get("type") in ["attribution", "status"]:
                            await websocket.send_json(item)
                        continue
                    
                    sentence = item
                    # Check for tool-related status updates in the first few characters
                    chk = sentence.strip().upper()
                    if "GET_AGENDA" in chk or "BOOK" in chk:
                        await websocket.send_json({"type": "status", "status": "checking_calendar"})
                    elif "GMAIL" in chk:
                        await websocket.send_json({"type": "status", "status": "reading_emails"})
                    elif "SLACK" in chk:
                        await websocket.send_json({"type": "status", "status": "checking_slack"})
                    elif "NOTION" in chk:
                        await websocket.send_json({"type": "status", "status": "taking_notes"})
                    
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
        print(f"WS: Client disconnected (session={session_id})")
    except Exception as e:
        print(f"WS: Error - {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up session memory
        memory_service.clear_session(session_id)
        print(f"WS: Connection closed (session={session_id})")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, ws="wsproto")
