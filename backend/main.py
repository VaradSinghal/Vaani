import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from services.asr_service import asr_service
from services.tts_service import tts_service
from services.logic_service import logic_service
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

@app.websocket("/voice-agent")
async def voice_agent_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    # Queue for incoming audio chunks from client
    audio_queue = asyncio.Queue()
    
    # Track if we are currently processing a response to avoid overlap
    response_in_progress = False

    async def client_audio_generator():
        while True:
            chunk = await audio_queue.get()
            if chunk is None: # EOS signal
                break
            yield chunk

    async def asr_callback(transcript: str, is_final: bool, language_code: str):
        nonlocal response_in_progress
        if response_in_progress:
            return

        print(f"ASR ({language_code}): {transcript} (Final: {is_final})")
        
        # Trigger response logic
        if is_final or len(transcript.split()) > 4:
            response_in_progress = True
            reply_text, lang = logic_service.generate_response(transcript, lang=language_code)
            print(f"Agent Reply ({lang}): {reply_text}")
            
            # Stream TTS back to client
            async for audio_chunk in tts_service.stream_tts(reply_text, lang):
                await websocket.send_bytes(audio_chunk)
            
            # Reset for next turn
            response_in_progress = False

    # Task to receive audio from client
    async def receive_from_client():
        try:
            while True:
                data = await websocket.receive()
                if "bytes" in data:
                    await audio_queue.put(data["bytes"])
                elif "text" in data:
                    # Handle text commands if any
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

    # Main orchestration task
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
