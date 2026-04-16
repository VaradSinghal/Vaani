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

    async def stream_chat(self, user_input: str, system_prompt: str = None):
        if not self.client:
            # Mock behavior
            print("LLM: Mocking response...")
            yield "नमस्ते! मैं आपकी क्या सहायता कर सकता हूँ?"
            return

        if not system_prompt:
            import datetime
            now_str = datetime.datetime.now().isoformat()
            system_prompt = (
                f"You are 'Vaani', a concise voice agent. Current time: {now_str}. "
                "To use a calendar tool, your very first characters MUST be a COMMAND STRING, nothing else. "
                "Commands:\n"
                "1. GET_AGENDA\n"
                "2. BOOK|Meeting Title|2026-04-16T15:00:00|2026-04-16T16:00:00\n"
                "3. DETAILS|Meeting Title\n"
                "4. CANCEL|Meeting Title\n"
                "To use, output JUST the command. Do not add formatting. "
                "If no tool is needed, respond naturally."
            )

        try:
            stream = await self.client.chat.completions(
                model="sarvam-105b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
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
                            chk = text_so_far.strip()
                            if chk.startswith("GET_") or chk.startswith("BOOK") or chk.startswith("DETA") or chk.startswith("CANC"):
                                is_tool_call = True
                            else:
                                yield text_so_far
                        elif is_tool_call:
                            text_so_far += content
                        else:
                            yield content
            
            if is_tool_call:
                # The LLM sometimes injects random newlines in ISO strings (e.g., 14:\n\n00). Clean it completely.
                tool_buffer = text_so_far.replace('\n', '').replace('\r', '').strip()
                
                # Instantly yield a filler phrase to trigger TTS! This drops perceived latency to ~0s!
                yield "एक मिनट, मैं चेक करती हूँ। "
                
                try:
                    from services.calendar_service import calendar_service
                    
                    if tool_buffer.startswith("GET_AGENDA"):
                        print(f"LLM TOOL: GET_AGENDA")
                        result = calendar_service.get_upcoming_events()
                    elif tool_buffer.startswith("BOOK|"):
                        parts = tool_buffer.split("|")
                        if len(parts) >= 4:
                            print(f"LLM TOOL: BOOK {parts[1]}")
                            result = calendar_service.schedule_event(
                                summary=parts[1].strip(),
                                start_time=parts[2].strip(),
                                end_time=parts[3].strip()
                            )
                        else:
                            result = f"Error: Malformed BOOK command: {tool_buffer}"
                    elif tool_buffer.startswith("DETAILS|"):
                        parts = tool_buffer.split("|")
                        if len(parts) >= 2:
                            print(f"LLM TOOL: DETAILS {parts[1]}")
                            result = calendar_service.get_event_details(parts[1].strip())
                        else:
                            result = "Error: Malformed DETAILS command."
                    elif tool_buffer.startswith("CANCEL|"):
                        parts = tool_buffer.split("|")
                        if len(parts) >= 2:
                            print(f"LLM TOOL: CANCEL {parts[1]}")
                            result = calendar_service.cancel_event(parts[1].strip())
                        else:
                            result = "Error: Malformed CANCEL command."
                    else:
                        result = f"Unknown command: {tool_buffer}"
                except Exception as e:
                    result = f"Tool failure: {str(e)}"
                    print(f"LLM TOOL ERROR: {result} - Buffer: {tool_buffer}")
                    
                follow_up = f"{system_prompt}\n\n[TOOL RESULT]:\n{result}\n\nConcisely summarize this result for the user in spoken format."
                second_stream = await self.client.chat.completions(
                    model="sarvam-105b",
                    messages=[
                        {"role": "system", "content": follow_up},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.4,
                    stream=True
                )
                async for chunk2 in second_stream:
                    if chunk2.choices and chunk2.choices[0].delta.content:
                        yield chunk2.choices[0].delta.content
                        
        except Exception as e:
            print(f"LLM Streaming Error: {e}")

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
