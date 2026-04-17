import os
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict

AGENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "agents")

class AgentService:
    def __init__(self):
        os.makedirs(AGENTS_DIR, exist_ok=True)
        # Create a default agent if none exists
        if not self.list_agents():
            self.create_default_agent()

    def list_agents(self) -> List[Dict]:
        """List all available agents."""
        agents = []
        for filename in os.listdir(AGENTS_DIR):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(AGENTS_DIR, filename), "r", encoding="utf-8") as f:
                        agents.append(json.load(f))
                except Exception as e:
                    print(f"AgentService: Error loading {filename}: {e}")
        return sorted(agents, key=lambda x: x.get("created_at", ""), reverse=True)

    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Retrieve a specific agent by ID."""
        path = os.path.join(AGENTS_DIR, f"{agent_id}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def create_agent(self, name: str, description: str, system_instructions: str, role: str = "general", tools_enabled: Optional[List[str]] = None, voice_id: str = "anushka") -> Dict:
        """Create and persist a new agent."""
        agent_id = str(uuid.uuid4())[:8]
        if tools_enabled is None:
            tools_enabled = ["GMAIL", "SLACK", "CALENDAR", "NOTION", "LIVE_READ"]
            
        agent_data = {
            "id": agent_id,
            "name": name,
            "description": description,
            "system_instructions": system_instructions,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "tools_enabled": tools_enabled,
            "voice_id": voice_id
        }
        
        path = os.path.join(AGENTS_DIR, f"{agent_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(agent_data, f, ensure_ascii=False, indent=2)
            
        print(f"AgentService: Created agent '{name}' ({agent_id})")
        return agent_data

    def update_agent(self, agent_id: str, updates: Dict) -> Optional[Dict]:
        """Update an existing agent's configuration."""
        path = os.path.join(AGENTS_DIR, f"{agent_id}.json")
        if not os.path.exists(path):
            return None
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                agent_data = json.load(f)
            
            # Update fields
            for key, value in updates.items():
                if key in ["name", "description", "system_instructions", "role", "tools_enabled", "voice_id"]:
                    agent_data[key] = value
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(agent_data, f, ensure_ascii=False, indent=2)
                
            print(f"AgentService: Successfully updated agent '{agent_id}' configuration. Tools: {agent_data.get('tools_enabled')}")
            return agent_data
        except Exception as e:
            print(f"AgentService: Error updating {agent_id}: {e}")
            return None

    def delete_agent(self, agent_id: str):
        """Remove an agent definition."""
        path = os.path.join(AGENTS_DIR, f"{agent_id}.json")
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def create_default_agent(self):
        """Create the standard Vaani agent."""
        self.create_agent(
            name="Vaani Core",
            description="The original polyglot assistant. Expert in productivity, research, and scheduling.",
            system_instructions="You are 'Vaani', an expert personal assistant. You help users with productivity, research, and task management.",
            role="general",
            tools_enabled=["GMAIL", "SLACK", "CALENDAR", "NOTION", "LIVE_READ"],
            voice_id="anushka"
        )

# Singleton instance
agent_service = AgentService()
