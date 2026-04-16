"""
Document Service — Intelligent Document Understanding.

Handles document upload, parsing, classification, and fact extraction.
Uses Sarvam Document Intelligence for scanned/image docs and PyPDF2 
as a fast fallback for text-based PDFs.

Problem Statement: Intelligent Document Understanding (Low-Cost)
- Cost-efficient: PyPDF2 fast path for text PDFs (zero API cost)
- Handle noisy inputs: Sarvam DocIntel for scanned/image documents
- Avoid naive LLM-only approach: Structured extraction pipeline
"""

import os
import io
import uuid
import asyncio
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads")


class DocumentService:
    """
    Document processing pipeline:
    1. Receive file (PDF, image, text)
    2. Extract text (PyPDF2 fast path or Sarvam DocIntel for scanned docs)
    3. Classify document type via LLM
    4. Extract atomic facts via LLM
    5. Vectorize facts and store in VectorStore
    """

    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        self._sarvam_client = None
        if self.api_key:
            from sarvamai import SarvamAI
            self._sarvam_client = SarvamAI(api_subscription_key=self.api_key)
            print("DocService: Initialized with Sarvam AI client")
        else:
            print("DocService: Running without Sarvam AI (PyPDF2 only)")

    async def process_document(
        self,
        file_bytes: bytes,
        filename: str,
        language: str = "en-IN",
    ) -> dict:
        """
        Full pipeline: Parse → Classify → Extract Facts → Vectorize.
        
        Returns:
            {
                "doc_id": str,
                "filename": str,
                "doc_type": str,
                "title": str,
                "fact_count": int,
                "facts": list[str],
                "processed_at": str,
            }
        """
        import time
        start_time = time.time()
        doc_id = str(uuid.uuid4())[:8]
        
        # Save file to disk
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(filename)[1].lower()
        save_path = os.path.join(UPLOAD_DIR, f"{doc_id}{ext}")
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        # Step 1: Extract text
        print(f"DocService: Processing '{filename}' ({len(file_bytes)} bytes)")
        
        extracted_text = ""
        if ext == ".pdf":
            # Try fast PyPDF2 extraction first
            extracted_text = self._extract_pdf_text(file_bytes)
            if len(extracted_text.strip()) < 50:
                # Very little text extracted — likely scanned PDF, use Sarvam DocIntel
                print("DocService: PDF appears scanned, trying Sarvam DocIntel...")
                extracted_text = await self._parse_with_sarvam(save_path, language)
        elif ext in (".png", ".jpg", ".jpeg", ".webp"):
            # Images always need Sarvam DocIntel (OCR)
            extracted_text = await self._parse_with_sarvam(save_path, language)
        elif ext in (".txt", ".md", ".csv"):
            extracted_text = file_bytes.decode("utf-8", errors="ignore")
        else:
            # Try as plain text
            try:
                extracted_text = file_bytes.decode("utf-8", errors="ignore")
            except Exception:
                extracted_text = await self._parse_with_sarvam(save_path, language)

        if not extracted_text or len(extracted_text.strip()) < 20:
            return {
                "doc_id": doc_id,
                "filename": filename,
                "doc_type": "unknown",
                "title": filename,
                "fact_count": 0,
                "facts": [],
                "error": "Could not extract meaningful text from document",
                "processed_at": datetime.now().isoformat(),
            }

        # Step 2 & 3: Parallel Metadata and Fact Extraction
        import time
        start_llm = time.time()
        
        # We run metadata extraction (title/type) and fact extraction in parallel
        metadata_task = self._extract_metadata(extracted_text[:1000], filename)
        facts_task = self._extract_facts(extracted_text, "document")
        
        metadata, facts = await asyncio.gather(metadata_task, facts_task)
        
        doc_type = metadata.get("doc_type", "document")
        title = metadata.get("title", filename)

        llm_duration = time.time() - start_llm
        print(f"DocService: LLM parallel processing took {llm_duration:.2f}s")

        # Step 4: Vectorize and store
        if facts:
            from services.vector_store import vector_store
            vector_store.add_facts(facts, doc_id, title, doc_type)
            vector_store.save_to_disk()

        result = {
            "doc_id": doc_id,
            "filename": filename,
            "doc_type": doc_type,
            "title": title,
            "fact_count": len(facts),
            "facts": facts,
            "processed_at": datetime.now().isoformat(),
        }
        
        print(f"DocService: Processed '{filename}' in {time.time() - start_time:.2f}s total")
        return result

    def get_full_text(self, doc_id: str) -> Optional[str]:
        """
        Retrieves the full raw parsed text of a document by its ID.
        Checks for existing markdown/text output in the parsed directory.
        """
        parsed_dir = os.path.join(UPLOAD_DIR, "parsed")
        if not os.path.exists(parsed_dir):
            return None

        # Look for files starting with doc_id
        for filename in os.listdir(parsed_dir):
            if filename.startswith(doc_id):
                path = os.path.join(parsed_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception as e:
                    print(f"DocService: Error reading parsed doc {doc_id}: {e}")
                    return None
        
        # Fallback: Check if it was a plain text/md file in the original uploads
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(doc_id):
                path = os.path.join(UPLOAD_DIR, filename)
                # If it's a text/md file, just read it
                if any(path.endswith(ext) for ext in ['.txt', '.md', '.csv']):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            return f.read()
                    except Exception:
                        pass
                # If it's a PDF, try to extract text on-the-fly if needed
                elif path.endswith('.pdf'):
                    with open(path, "rb") as f:
                        return self._extract_pdf_text(f.read())
                # If it's an image, we'd need DocIntel (skip for now to avoid long blocking)

        return None

    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        """Fast local PDF text extraction using PyPDF2. Zero API cost."""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text_parts = []
            for page in reader.pages[:20]:  # Cap at 20 pages for cost efficiency
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n\n".join(text_parts)
        except Exception as e:
            print(f"DocService: PyPDF2 extraction failed: {e}")
            return ""

    async def _parse_with_sarvam(self, file_path: str, language: str = "en-IN") -> str:
        """
        Use Sarvam Document Intelligence for OCR + layout extraction.
        Handles scanned PDFs, images, and noisy documents.
        """
        if not self._sarvam_client:
            print("DocService: Sarvam client not available for DocIntel")
            return ""

        try:
            job = self._sarvam_client.document_intelligence.create_job(
                language=language,
                output_format="md"
            )
            
            # Upload and start processing
            job.upload_file(file_path)
            job.start()
            
            # Poll for completion (runs in thread to avoid blocking)
            result = await asyncio.to_thread(job.wait_until_complete)
            
            # Download the parsed output
            output_dir = os.path.join(UPLOAD_DIR, "parsed")
            os.makedirs(output_dir, exist_ok=True)
            job.download_output(output_dir)
            
            # Read the output markdown file
            output_files = [f for f in os.listdir(output_dir) if f.endswith(('.md', '.html'))]
            if output_files:
                output_path = os.path.join(output_dir, output_files[-1])
                with open(output_path, "r", encoding="utf-8") as f:
                    return f.read()
            
            return ""
        except Exception as e:
            print(f"DocService: Sarvam DocIntel failed: {e}")
            import traceback
            traceback.print_exc()
            return ""

    async def _extract_metadata(self, text_preview: str, filename: str) -> dict:
        """
        Combine classification and titling into one fast LLM call.
        Uses sarvam-30b for lower latency.
        """
        if not self._sarvam_client:
            return {"doc_type": "document", "title": filename}

        try:
            from sarvamai import AsyncSarvamAI
            async_client = AsyncSarvamAI(api_subscription_key=self.api_key)
            
            prompt = (
                "Analyze the following document preview and extract meta-information.\n"
                "Return a JSON object with exactly two keys: 'doc_type' and 'title'.\n\n"
                "Constraints:\n"
                "- doc_type: one of [invoice, receipt, report, letter, form, contract, resume, certificate, id_card, bank_statement, medical, other]\n"
                "- title: a concise title (max 5 words)\n\n"
                f"Filename: {filename}\n"
                f"Content preview:\n{text_preview[:800]}"
            )
            
            response = await async_client.chat.completions(
                model="sarvam-30b", # Using faster model for metadata
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                stream=False
            )
            
            raw = response.choices[0].message.content.strip()
            # Basic JSON extraction for robustness
            import json
            import re
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"doc_type": "document", "title": filename}
        except Exception as e:
            print(f"DocService: Metadata extraction failed: {e}")
            return {"doc_type": "document", "title": filename}

    async def _extract_facts(self, document_text: str, doc_type: str) -> list[str]:
        """
        Extract atomic, searchable facts from document text using LLM.
        
        This is the core of the RAG-less approach:
        - Instead of chunking raw text, we extract structured facts
        - Each fact is self-contained and searchable
        - Facts are embedded once and stored forever
        """
        if not self._sarvam_client:
            # Fallback: split into sentences as "facts"
            sentences = [s.strip() for s in document_text.split('.') if len(s.strip()) > 20]
            return sentences[:15]

        try:
            from sarvamai import AsyncSarvamAI
            async_client = AsyncSarvamAI(api_subscription_key=self.api_key)
            
            # Truncate to stay within context limits
            truncated = document_text[:4000]
            
            prompt = (
                f"You are a fact extraction engine. Extract 10-20 atomic, self-contained facts "
                f"from this {doc_type}. Each fact should be a single statement that can be "
                f"understood without context. Include all key details: names, numbers, dates, "
                f"amounts, addresses, etc.\n\n"
                f"Rules:\n"
                f"- Each fact on a new line\n"
                f"- Start each fact with a dash (-)\n"
                f"- Be specific (include actual values, not 'some amount')\n"
                f"- Include both Hindi and English terms if present\n"
                f"- Max 20 facts\n\n"
                f"Document:\n{truncated}"
            )
            
            response = await async_client.chat.completions(
                model="sarvam-105b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                stream=False
            )
            
            raw_response = response.choices[0].message.content.strip()
            
            # Parse facts from the response
            facts = []
            for line in raw_response.split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    fact = line.lstrip('- ').strip()
                    if len(fact) > 10:  # Skip trivially short facts
                        facts.append(fact)
                elif len(line) > 15 and not line.startswith('#'):
                    # Also capture lines that aren't dash-prefixed
                    facts.append(line)
            
            return facts[:20]  # Cap at 20 facts
        except Exception as e:
            print(f"DocService: Fact extraction failed: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to sentence splitting
            sentences = [s.strip() for s in document_text.split('.') if len(s.strip()) > 20]
            return sentences[:15]


# Singleton instance
document_service = DocumentService()
