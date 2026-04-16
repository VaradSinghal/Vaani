import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd()))

from services.document_service import document_service
from services.translate_service import translate_service
from services.llm_service import llm_service

async def test_live_read_pipeline():
    print("--- Starting Live Read Pipeline Test ---")
    
async def test_live_read_pipeline():
    print("--- Starting Live Read Pipeline Test ---")
    
    # 1. Check Document Retrieval
    # We need a doc_id that actually exists. I'll check the uploads dir.
    upload_dir = os.path.join("data", "uploads", "parsed")
    if not os.path.exists(upload_dir) or not os.listdir(upload_dir):
        print("[ERROR] No parsed documents found to test with. Please upload a PDF first.")
        # Try to find any doc_id in the base upload dir as fallback
        base_dir = os.path.join("data", "uploads")
        if os.path.exists(base_dir) and os.listdir(base_dir):
            doc_id = os.listdir(base_dir)[0].split('.')[0]
            print(f"[INFO] Using fallback doc_id from base uploads: {doc_id}")
        else:
            return

    if 'doc_id' not in locals():
        doc_id = os.listdir(upload_dir)[0].split('.')[0]
    
    print(f"[OK] Found test document ID: {doc_id}")
    
    raw_text = document_service.get_full_text(doc_id)
    if raw_text:
        print(f"[OK] Successfully retrieved full text ({len(raw_text)} chars)")
        print(f"   Snippet: {raw_text[:100]}...")
    else:
        print("[ERROR] Failed to retrieve full text.")
        return

    # 2. Test Translation
    print("\n--- Testing Mayura Translation (en -> hi) ---")
    sample_chunk = "Vaani is a multilingual voice agent designed for high-performance productivity."
    translated = translate_service.translate_text(sample_chunk, "hi-IN")
    print(f"   Original: {sample_chunk}")
    print(f"   Translated: {translated}")
    
    if "Error" not in translated and translated != sample_chunk:
        print("[OK] Translation verified.")
    else:
        print("[ERROR] Translation failed or returned error.")

    # 3. Test Full Pipeline (Mocked Queue)
    print("\n--- Testing Full LLM Trigger (Mocked ID) ---")
    tts_queue = asyncio.Queue()
    
    # Simulating a user query that triggers LIVE_READ
    user_query = f"Read the document {doc_id} to me in Hindi."
    print(f"User Query: {user_query}")
    
    gen = llm_service.stream_chat(
        user_input=user_query,
        session_id="test_session",
        user_id="test_user",
        tts_queue=tts_queue
    )
    
    print("Processing stream...")
    async for item in gen:
        if isinstance(item, dict):
            print(f"   Status/Attr: {item}")
        else:
            print(f"   Chat Token: {item}")

    print(f"\n[OK] Pipeline stream finished. TTS Queue size: {tts_queue.qsize()}")
    while not tts_queue.empty():
        chunk = await tts_queue.get()
        print(f"   [QUEUE ITEM-UTF8]: {chunk.encode('utf-8')}") # Encode to avoid print errors for non-ascii

if __name__ == "__main__":
    asyncio.run(test_live_read_pipeline())
