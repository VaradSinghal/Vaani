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

    async def stream_chat(self, user_input: str, session_id: str = None, user_id: str = None, system_prompt: str = None):
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
            system_prompt = (
                f"You are 'Vaani', an expert personal assistant. Current time: {now_str}. "
                "You have access to DOCUMENT KNOWLEDGE (uploaded files) and USER MEMORY (past facts). "
                "IMPORTANT: If a tool needs info (email, name, date) that is in your KNOWLEDGE or MEMORY, use it automatically! "
                "Example: If user says 'Email the invoice total', search DOCUMENT KNOWLEDGE for the total first.\n\n"
                "To use a tool, start with a COMMAND STRING:\n"
                "1. GET_AGENDA\n"
                "2. BOOK|Title|StartISO|EndISO\n"
                "3. DETAILS|Title\n"
                "4. CANCEL|Title\n"
                "5. GMAIL_READ\n"
                "6. GMAIL_SEND|recipient|subject|body\n"
                "7. NOTION_NOTE|text\n"
                "8. SLACK_READ|channel\n"
                "9. SLACK_MSG|channel|text\n"
                "Output ONLY the command. If no tool is needed, respond naturally."
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
                model="sarvam-105b",
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
                            if not text_so_far.strip() or len(text_so_far.strip()) < 4: continue
                            first_chunk = False
                            chk = text_so_far.strip().upper()
                            # Check for any tool prefix in the first line of output
                            tool_prefixes = ["GET_", "BOOK", "DETA", "CANC", "GMAI", "NOTI", "SLAC"]
                            if any(chk.startswith(p) for p in tool_prefixes):
                                is_tool_call = True
                            else:
                                yield text_so_far
                        elif is_tool_call:
                            text_so_far += content
                        else:
                            yield content
            
            # Collect full response text for memory storage
            full_response = text_so_far if not is_tool_call else ""

            if is_tool_call:
                # The LLM sometimes injects random newlines. Clean it completely.
                tool_buffer = text_so_far.replace('\n', '').replace('\r', '').strip()
                
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
                    else:
                        result = f"Unknown command: {tool_buffer}"
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
