"""
Conversational Memory Service — Short-term + Long-term memory.

Manages multi-turn conversation history (per session) and persistent 
user facts (across sessions). Integrates with VectorStore for document
knowledge retrieval.

Problem Statement: Conversational Memory Layer
- Memory relevance: Only inject relevant document facts via vector search
- Cost efficiency: Sliding window of 8 turns, max 20 user facts
- Context prioritization: Document facts > user facts > old history
"""

import os
import json
import asyncio
import threading
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

USER_FACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "user_facts")


class MemoryService:
    """
    Unified memory manager with three layers:
    
    1. Short-term (session): Last 8 turns of conversation history
    2. Long-term (user facts): Persistent preferences/contacts/habits
    3. Knowledge (documents): Semantic search over uploaded document facts
    """

    def __init__(self):
        self.sessions: dict[str, list[dict]] = {}  # session_id -> [{role, content}]
        self.user_facts: dict[str, list[str]] = {}  # user_id -> ["prefers Hindi", ...]
        self.user_locks: dict[str, threading.Lock] = {} # Per-user lock for persistence
        self._global_lock = threading.Lock()
        self.MAX_TURNS = 8       # Keep last 8 turn-pairs in session
        self.MAX_USER_FACTS = 20  # Max persistent facts per user

    def _get_user_lock(self, user_id: str) -> threading.Lock:
        if user_id not in self.user_locks:
            with self._global_lock:
                if user_id not in self.user_locks:
                    self.user_locks[user_id] = threading.Lock()
        return self.user_locks[user_id]

    # ─── Short-term Memory (Session) ──────────────────────────────────

    def add_turn(self, session_id: str, role: str, content: str):
        """Add a message to session history. Auto-trims to MAX_TURNS pairs."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append({
            "role": "user" if role.lower() == "user" else "assistant",
            "content": content,
        })

        # Trim to MAX_TURNS * 2 messages (user + assistant pairs)
        max_messages = self.MAX_TURNS * 2
        if len(self.sessions[session_id]) > max_messages:
            self.sessions[session_id] = self.sessions[session_id][-max_messages:]

    def get_history(self, session_id: str) -> list[dict]:
        """Get formatted chat history for LLM context."""
        return self.sessions.get(session_id, [])

    def clear_session(self, session_id: str):
        """Clean up session memory on disconnect."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            print(f"Memory: Cleared session {session_id}")

    # ─── Long-term Memory (User Facts) ───────────────────────────────

    def get_user_facts(self, user_id: str) -> list[str]:
        """Get persistent facts about a user."""
        if user_id not in self.user_facts:
            self._load_user_facts(user_id)
        return self.user_facts.get(user_id, [])

    async def extract_and_save_facts(self, user_id: str, user_msg: str, agent_msg: str):
        """
        Extract memorable facts from a conversation turn and persist them.
        Runs async (fire-and-forget) to not block the response pipeline.
        """
        if not user_id or user_id == "anonymous":
            return

        try:
            api_key = os.getenv("SARVAM_API_KEY")
            if not api_key:
                return

            from sarvamai import AsyncSarvamAI
            client = AsyncSarvamAI(api_subscription_key=api_key)

            prompt = (
                "You are a HIGH-PRECISION fact extraction engine for a voice assistant. "
                "Extract any NEW, PERMANENT facts about the user from this conversation turn. "
                "Facts include: names, specific preferences (food/language/work), contact info, "
                "favorite places, work habits, or recurring meetings.\n\n"
                "Rules:\n"
                "- ONLY extract facts mentioned BY THE USER.\n"
                "- Do NOT extract temporary info (e.g., 'user is busy now').\n"
                "- Do NOT extract agent actions (e.g., 'agent sent email').\n"
                "- Each fact on a new line starting with -\n"
                "- If there are no new memorable facts, respond with ONLY: NONE\n"
                "- Max 3 facts per turn. Be concise.\n\n"
                f"User said: {user_msg}\n"
                f"Agent responded: {agent_msg[:300]}"
            )

            response = await client.chat.completions(
                model="sarvam-105b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                stream=False
            )

            raw = response.choices[0].message.content.strip()
            
            if "NONE" in raw.upper():
                return

            new_facts = []
            for line in raw.split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    fact = line.lstrip('- ').strip()
                    if len(fact) > 10:
                        new_facts.append(fact)

            if new_facts:
                self._merge_user_facts(user_id, new_facts)
                print(f"Memory: Extracted {len(new_facts)} new facts for user {user_id[:6]}...")

        except Exception as e:
            print(f"Memory: Fact extraction failed (non-blocking): {e}")

    def _merge_user_facts(self, user_id: str, new_facts: list[str]):
        """Merge new facts with existing ones, deduplicating similar facts."""
        if user_id not in self.user_facts:
            self._load_user_facts(user_id)

        existing = self.user_facts.get(user_id, [])
        
        for new_fact in new_facts:
            # Simple dedup: skip if a very similar fact already exists
            is_duplicate = False
            new_lower = new_fact.lower()
            for existing_fact in existing:
                if (new_lower in existing_fact.lower() or 
                    existing_fact.lower() in new_lower):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                existing.append(new_fact)

        # Cap at MAX_USER_FACTS
        if len(existing) > self.MAX_USER_FACTS:
            existing = existing[-self.MAX_USER_FACTS:]

        with self._get_user_lock(user_id):
            self.user_facts[user_id] = existing
            self._save_user_facts(user_id)

    def _load_user_facts(self, user_id: str):
        """Load user facts from disk."""
        path = os.path.join(USER_FACTS_DIR, f"{user_id}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.user_facts[user_id] = data.get("facts", [])
                print(f"Memory: Loaded {len(self.user_facts[user_id])} facts for user {user_id[:6]}...")
            except Exception as e:
                print(f"Memory: Failed to load user facts: {e}")
                self.user_facts[user_id] = []
        else:
            self.user_facts[user_id] = []

    def _save_user_facts(self, user_id: str):
        """Persist user facts to disk."""
        os.makedirs(USER_FACTS_DIR, exist_ok=True)
        path = os.path.join(USER_FACTS_DIR, f"{user_id}.json")
        try:
            data = {
                "user_id": user_id,
                "facts": self.user_facts.get(user_id, []),
                "updated_at": datetime.now().isoformat(),
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Memory: Failed to save user facts: {e}")

    # ─── Context Builder ─────────────────────────────────────────────

    def build_augmented_prompt(
        self,
        session_id: str,
        user_id: str,
        user_query: str,
        base_system_prompt: str,
    ) -> tuple[str, list[dict], dict]:
        """
        Build a memory-augmented system prompt + message history + attribution data.
        
        Returns:
            (augmented_system_prompt, message_history, attribution_metadata)
        """
        memory_sections = []
        attribution = {"sources": []}

        # --- Document Knowledge (RAG-less vector search) ---
        try:
            from services.vector_store import vector_store
            if vector_store.total_facts > 0:
                results = vector_store.search(user_query, top_k=5, min_score=0.35)
                if results:
                    facts_text = ""
                    for r in results:
                        facts_text += f"  - [{r.doc_title}] {r.text}\n"
                        if r.doc_title not in attribution["sources"]:
                            attribution["sources"].append(r.doc_title)
                    
                    memory_sections.append(
                        f"[DOCUMENT KNOWLEDGE — relevant info from your uploaded files]:\n{facts_text.strip()}"
                    )
        except Exception as e:
            print(f"Memory: Vector search failed: {e}")

        # --- User Facts (long-term memory) ---
        if user_id and user_id != "anonymous":
            facts = self.get_user_facts(user_id)
            if facts:
                facts_text = "\n".join(f"  - {f}" for f in facts)
                memory_sections.append(
                    f"[USER MEMORY — things you remember about this user]:\n{facts_text}"
                )

        # --- Build augmented system prompt ---
        augmented = base_system_prompt
        if memory_sections:
            augmented += "\n\n" + "\n\n".join(memory_sections)
            augmented += (
                "\n\nUse the above knowledge naturally in your responses. "
                "If the user asks about their documents, use DOCUMENT KNOWLEDGE. "
                "If you know something about the user from USER MEMORY, use it naturally."
            )

    # --- Session History ---
        history = self.get_history(session_id) if session_id else []

        return augmented, history, attribution


# Singleton instance
memory_service = MemoryService()
