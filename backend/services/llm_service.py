import asyncio
from sarvamai import AsyncSarvamAI
import os
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        if self.api_key:
            self.client = AsyncSarvamAI(api_subscription_key=self.api_key)
            print("LLM: Initialized with Sarvam AI client")
        else:
            self.client = None
            print("LLM: Running in MOCK mode (no API key found)")

    async def stream_chat(self, user_input: str, session_id: str = None, user_id: str = None, system_prompt: str = None, tts_queue: asyncio.Queue = None, agent_id: str = None):
        """Stream chat with memory-augmented context."""
        if not self.client:
            # Mock behavior
            print("LLM: Mocking response...")
            yield "नमस्ते! मैं आपकी क्या सहायता कर सकता हूँ?"
            return

        # Build base system prompt with tool commands
        if not system_prompt:
            import datetime
            now_str = datetime.datetime.now().isoformat()
            
            # Fetch custom agent instructions if agent_id is provided
            base_instructions = "You are 'Vaani', an expert personal assistant. You help users with productivity, research, and task management."
            tools_to_inject = ["GMAIL", "SLACK", "CALENDAR", "NOTION", "LIVE_READ"] # Default
            
            if agent_id:
                from services.agent_service import agent_service
                agent = agent_service.get_agent(agent_id)
                if agent:
                    base_instructions = agent.get("system_instructions", base_instructions)
                    tools_to_inject = agent.get("tools_enabled", tools_to_inject)
            
            # Map tool IDs to prompt strings
            tool_definitions = {
                "GMAIL": "5. GMAIL_READ\n6. GMAIL_SEND|recipient|subject|body\n",
                "SLACK": "8. SLACK_READ|channel\n9. SLACK_MSG|channel|text\n",
                "NOTION": "7. NOTION_NOTE|text\n",
                "CALENDAR": "1. GET_AGENDA\n2. BOOK|Title|StartISO|EndISO\n3. DETAILS|Title\n4. CANCEL|Title\n",
                "LIVE_READ": "10. LIVE_READ|doc_id|target_lang\n"
            }
            
            injected_tools_str = ""
            for tool_id in tools_to_inject:
                if tool_id in tool_definitions:
                    injected_tools_str += tool_definitions[tool_id]

            # Fetch available documents to avoid asking user for IDs
            from services.vector_store import vector_store
            docs = vector_store.get_documents()
            doc_list_str = "\n".join([f"- {d['title']} (ID: {d['doc_id']})" for d in docs]) if docs else "None"
            
            system_prompt = (
                f"{base_instructions}\n"
                f"Current time: {now_str}. "
                "You have access to DOCUMENT KNOWLEDGE (uploaded files) and USER MEMORY (past facts). "
                "IMPORTANT: If a tool needs info (email, name, date) that is in your KNOWLEDGE or MEMORY, use it automatically! "
                "Example: If user says 'Email the invoice total', search DOCUMENT KNOWLEDGE for the total first.\n\n"
                f"[AVAILABLE DOCUMENTS (ID resolution list)]:\n{doc_list_str}\n\n"
                "To use a tool, start with a COMMAND STRING:\n"
                f"{injected_tools_str}"
                "CRITICAL: If a user asks to 'read' or 'open' a file, find the matching ID from the AVAILABLE DOCUMENTS list and use the LIVE_READ command. "
                "DO NOT ask the user for a document ID if the title is in the list. Output ONLY the raw command string. "
                "For normal conversation, NEVER wrap your response in quotes."
            )

        # Augment system prompt with memory context (document facts + user facts)
        from services.memory_service import memory_service
        augmented_prompt, history, attribution = memory_service.build_augmented_prompt(
            session_id=session_id,
            user_id=user_id,
            user_query=user_input,
            base_system_prompt=system_prompt,
        )
        base_system_for_tools = system_prompt  # Keep un-augmented version for tool follow-up

        try:
            # Yield attribution to frontend if documents were retrieved
            if attribution.get("sources"):
                yield {"type": "attribution", "sources": attribution["sources"]}

            # Build messages with memory: system + history + current user input
            messages = [{"role": "system", "content": augmented_prompt}]
            messages.extend(history)  # Previous turns from session memory
            messages.append({"role": "user", "content": user_input})

            stream = await self.client.chat.completions(
                model="sarvam-30b",
                messages=messages,
                temperature=0.7,
                stream=True
            )
            
            is_tool_call = False
            first_chunk = True
            text_so_far = ""
            
            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        content = delta.content
                        if first_chunk:
                            text_so_far += content
                            # Strip common LLM prefixes for detection
                            chk = text_so_far.strip().upper()
                            chk = chk.replace("COMMAND:", "").replace("TOOL:", "").replace("ACTION:", "").replace("`", "").strip()
                            
                            # If after cleaning we have no actual identifier, continue collecting until we do
                            if not chk or len(chk) < 3: continue
                            
                            first_chunk = False
                            # Aggressive check: if it looks like a tool call (contains | and a known prefix), catch it
                            tool_prefixes = ["GET_", "BOOK", "DETA", "CANC", "GMAI", "NOTI", "SLAC", "LIVE"]
                            if any(chk.startswith(p) for p in tool_prefixes) or ("|" in chk and any(p in chk for p in tool_prefixes)):
                                is_tool_call = True
                            else:
                                cleaned = text_so_far.replace('"', '').replace('--', ' ')
                                yield cleaned
                        elif is_tool_call:
                            text_so_far += content
                        else:
                            # Clean conversational text as we stream
                            cleaned = content.replace('"', '').replace('--', ' ')
                            yield cleaned
            
            # Collect full response text for memory storage
            full_response = text_so_far if not is_tool_call else ""

            if is_tool_call:
                # The LLM sometimes injects random newlines or prefixes like 'COMMAND:'. Clean it completely.
                tool_buffer = text_so_far.replace('\n', '').replace('\r', '').strip()
                t_prefixes = ["COMMAND:", "TOOL:", "ACTION:", "`"]
                for p in t_prefixes:
                    if tool_buffer.upper().startswith(p):
                        tool_buffer = tool_buffer[len(p):].strip()
                
                # Instantly yield a filler phrase to trigger TTS! This drops perceived latency to ~0s!
                yield "एक मिनट, मैं चेक करती हूँ। "
                
                try:
                    from services.calendar_service import calendar_service
                    from services.gmail_service import gmail_service
                    from services.notion_service import notion_service
                    from services.slack_service import slack_service
                    
                    if tool_buffer.startswith("GET_AGENDA"):
                        result = calendar_service.get_upcoming_events()
                    elif tool_buffer.startswith("BOOK|"):
                        parts = tool_buffer.split("|")
                        if len(parts) >= 4:
                            result = calendar_service.schedule_event(summary=parts[1].strip(), start_time=parts[2].strip(), end_time=parts[3].strip())
                        else:
                            result = f"Error: Malformed BOOK command."
                    elif tool_buffer.startswith("DETAILS|"):
                        parts = tool_buffer.split("|")
                        result = calendar_service.get_event_details(parts[1].strip()) if len(parts) >= 2 else "Error: Malformed DETAILS."
                    elif tool_buffer.startswith("CANCEL|"):
                        parts = tool_buffer.split("|")
                        result = calendar_service.cancel_event(parts[1].strip()) if len(parts) >= 2 else "Error: Malformed CANCEL."
                    elif tool_buffer.startswith("GMAIL_READ"):
                        result = gmail_service.get_unread_emails()
                    elif tool_buffer.startswith("GMAIL_SEND|"):
                        parts = tool_buffer.split("|")
                        if len(parts) >= 4:
                            result = gmail_service.send_email(to=parts[1].strip(), subject=parts[2].strip(), body=parts[3].strip())
                        else:
                            result = "Error: Malformed GMAIL_SEND."
                    elif tool_buffer.startswith("NOTION_NOTE|"):
                        parts = tool_buffer.split("|")
                        result = notion_service.append_voice_note(parts[1].strip()) if len(parts) >= 2 else "Error: Malformed NOTION_NOTE."
                    elif tool_buffer.startswith("SLACK_READ|"):
                        parts = tool_buffer.split("|")
                        result = slack_service.read_latest_messages(parts[1].strip()) if len(parts) >= 2 else "Error: Malformed SLACK_READ."
                    elif tool_buffer.startswith("SLACK_MSG|"):
                        parts = tool_buffer.split("|")
                        if len(parts) >= 3:
                            result = slack_service.send_message(channel=parts[1].strip(), text=parts[2].strip())
                        else:
                            result = "Error: Malformed SLACK_MSG."
                    elif tool_buffer.startswith("LIVE_READ|"):
                        parts = tool_buffer.split("|")
                        if len(parts) >= 3:
                            doc_id = parts[1].strip()
                            target_lang = parts[2].strip()
                            
                            from services.document_service import document_service
                            from services.translate_service import translate_service
                            
                            # 1. Fetch raw text
                            raw_text = document_service.get_full_text(doc_id)
                            if not raw_text:
                                result = f"I'm sorry, I couldn't find the full text for that document (ID: {doc_id})."
                            else:
                                # 2. Indicate starting status
                                yield {"type": "status", "status": "reading_document"}
                                
                                # 3. Chunk and Translate -> TTS
                                chunks = [c.strip() for c in raw_text.split('\n') if len(c.strip()) > 10]
                                
                                read_count = 0
                                for chunk in chunks[:15]: # Cap at 15 paragraphs for safety
                                    translated = translate_service.translate_text(
                                        text=chunk, 
                                        target_lang=target_lang
                                    )
                                    if tts_queue:
                                        await tts_queue.put(translated)
                                    read_count += 1
                                    
                                result = f"I have finished reading {read_count} sections of the document to you in {target_lang}."
                        else:
                            result = "Error: Malformed LIVE_READ command. Expected: LIVE_READ|doc_id|target_lang."
                    else:
                        result = f"I tried to use a tool but it wasn't recognized. Command: {tool_buffer}"
                except Exception as e:
                    result = f"Tool failure: {str(e)}"
                    print(f"LLM TOOL ERROR: {result} - Buffer: {tool_buffer}")
                    
                # Unified summary: include both the tool result AND the memory context 
                # so the agent can reason across both (e.g., "I added it to the Notion page we discussed").
                follow_up = f"{augmented_prompt}\n\n[TOOL RESULT]:\n{result}\n\nConcisely summarize this result for the user in spoken format."
                
                second_stream = await self.client.chat.completions(
                    model="sarvam-105b",
                    messages=[
                        {"role": "system", "content": follow_up},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.4,
                    stream=True
                )
                tool_response_text = ""
                async for chunk2 in second_stream:
                    if chunk2.choices and chunk2.choices[0].delta.content:
                        tool_response_text += chunk2.choices[0].delta.content
                        yield chunk2.choices[0].delta.content
                full_response = tool_response_text
                        
        except Exception as e:
            print(f"LLM Streaming Error: {e}")
            return

        # --- Post-response memory updates (non-blocking) ---
        if session_id and full_response:
            # Store turn in session memory
            memory_service.add_turn(session_id, "user", user_input)
            memory_service.add_turn(session_id, "assistant", full_response)

        if user_id and user_id != "anonymous" and full_response:
            # Extract and persist user facts - AWAIT for synchronicity if session_id is active
            await memory_service.extract_and_save_facts(user_id, user_input, full_response)

    async def generate_title(self, user_input: str) -> str:
        if not self.client:
            return "Mock Session"
            
        system_prompt = (
            "Generate a very short, concise title (max 4 words) summarizing the following user message. "
            "Do not include quotes or any extra text, just the topic."
        )
        title = ""
        try:
            stream = await self.client.chat.completions(
                model="sarvam-105b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3,
                stream=True
            )
            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        title += delta.content
            return title.strip('"\' \n').title()[:50]
        except Exception as e:
            print(f"LLM Title Gen Error: {e}")
            return "New Chat"

llm_service = LLMService()
