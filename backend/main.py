import asyncio
import json
import re
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

app = FastAPI()

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
    print("Client connected")

    audio_queue = asyncio.Queue()
    response_in_progress = False

    async def client_audio_generator():
        while True:
            chunk = await audio_queue.get()
            if chunk is None: break
            yield chunk

    async def asr_callback(transcript: str, is_final: bool, language_code: str):
        nonlocal response_in_progress
        if response_in_progress:
            return

        print(f"ASR ({language_code}): {transcript} (Final: {is_final})")
        
        if is_final:
            response_in_progress = True
            print(f"Agent: Generating LLM response for: {transcript}")
            
            # Start LLM stream
            llm_gen = llm_service.stream_chat(transcript)
            
            # Pipe LLM -> Sentence Buffer -> TTS -> Client
            async for sentence in sentence_stream(llm_gen):
                print(f"LLM Sentence: {sentence}")
                async for audio_chunk in tts_service.stream_tts(sentence, language_code):
                    await websocket.send_bytes(audio_chunk)
            
            response_in_progress = False

    async def receive_from_client():
        try:
            while True:
                data = await websocket.receive()
                if "bytes" in data:
                    await audio_queue.put(data["bytes"])
                elif "text" in data:
                    msg = json.loads(data["text"])
                    if msg.get("type") == "eos":
                        await audio_queue.put(None)
                        break
        except WebSocketDisconnect:
            print("Client disconnected")
            await audio_queue.put(None)
        except Exception as e:
            print(f"Receive Error: {e}")
            await audio_queue.put(None)

    try:
        receive_task = asyncio.create_task(receive_from_client())
        asr_task = asyncio.create_task(asr_service.stream_asr(client_audio_generator(), asr_callback))
        await asyncio.gather(receive_task, asr_task)
    except Exception as e:
        print(f"Main Loop Error: {e}")
    finally:
        print("Closing connection")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
