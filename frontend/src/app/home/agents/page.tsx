"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { AgentCreatorModal } from "../../../components/AgentCreatorModal";

interface Agent {
  id: string;
  name: string;
  description: string;
  role: string;
  tools_enabled: string[];
  created_at: string;
}

const TOOL_BADGES: Record<string, string> = {
  GMAIL: "GMAIL",
  SLACK: "SLACK",
  NOTION: "NOTION",
  CALENDAR: "CAL",
  LIVE_READ: "DOCS"
};

export default function AgentStudio() {
  const { user } = useAuth();
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/agents");
      const data = await res.json();
      setAgents(data.agents || []);
    } catch (err) {
      console.error("Failed to fetch agents:", err);
    } finally {
      setLoading(false);
    }
  };

  const deleteAgent = async () => {
    if (!deleteConfirmId) return;
    try {
      await fetch(`http://127.0.0.1:8000/api/agents/${deleteConfirmId}`, { method: "DELETE" });
      setDeleteConfirmId(null);
      fetchAgents();
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const handleEditAgent = (agent: Agent) => {
    setSelectedAgent(agent);
    setIsModalOpen(true);
  };

  const handleCreateNew = () => {
    setSelectedAgent(null);
    setIsModalOpen(true);
  };

  return (
    <div className="flex-1 h-screen overflow-y-auto bg-[#fdfcf9] p-8 lg:p-12 relative">
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Header */}
        <div className="flex items-end justify-between border-b border-black/[0.05] pb-8">
          <div className="space-y-2">
            <h1 className="display-hero !text-6xl tracking-tighter">Agent Studio</h1>
            <p className="body-standard max-w-md text-black/40 italic">Design and deploy specialized autonomous agents tailored to your business needs.</p>
          </div>
          <button
            onClick={handleCreateNew}
            className="px-6 py-3 bg-[#2d2c25] text-white rounded-full font-medium hover:scale-105 transition-all active:scale-95 shadow-lg shadow-black/10"
          >
            + Create New Agent
          </button>
        </div>

        {/* Gallery */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-64 bg-black/5 rounded-[32px]" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className="group relative bg-white border border-black/[0.03] rounded-[40px] p-8 shadow-xl shadow-black/[0.02] hover:shadow-2xl hover:shadow-black/[0.05] transition-all duration-500 hover:-translate-y-1 overflow-hidden"
              >
                {/* Deletion Overlay */}
                {deleteConfirmId === agent.id && (
                  <div className="absolute inset-0 z-20 bg-white/90 backdrop-blur-md p-8 flex flex-col items-center justify-center text-center animate-in fade-in duration-300">
                    <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center mb-4">
                      <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </div>
                    <h4 className="text-lg font-bold text-black mb-1">Delete Agent?</h4>
                    <p className="text-xs text-black/40 mb-6 px-4">This action cannot be undone. Profile, memory, and settings will be purged.</p>
                    <div className="flex items-center gap-3 w-full">
                      <button 
                        onClick={() => setDeleteConfirmId(null)}
                        className="flex-1 py-3 bg-black/5 hover:bg-black/10 rounded-2xl text-xs font-bold transition-all"
                      >
                        Cancel
                      </button>
                      <button 
                        onClick={deleteAgent}
                        className="flex-1 py-3 bg-red-500 text-white rounded-2xl text-xs font-bold hover:bg-red-600 transition-all shadow-lg shadow-red-500/20"
                      >
                        Confirm
                      </button>
                    </div>
                  </div>
                )}

                <div className="flex flex-col h-full space-y-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="section-heading !text-3xl tracking-tight">{agent.name}</h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => handleEditAgent(agent)}
                        className="opacity-0 group-hover:opacity-40 hover:!opacity-100 p-2 text-black transition-opacity"
                        title="Configure Agent"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                      </button>
                      <button 
                        onClick={() => setDeleteConfirmId(agent.id)}
                        className="opacity-0 group-hover:opacity-40 hover:!opacity-100 p-2 text-black transition-opacity"
                        title="Delete Agent"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  {/* Active Tools Row */}
                  <div className="flex flex-wrap gap-1.5 overflow-hidden">
                    {agent.tools_enabled?.map(toolId => (
                      <div key={toolId} className="px-2 py-1 rounded-md bg-black/[0.03] border border-black/[0.05] flex items-center justify-center text-[8px] font-mono font-bold text-black/40 hover:text-black/80 transition-all cursor-default" title={toolId}>
                        {TOOL_BADGES[toolId] || "TOOL"}
                      </div>
                    ))}
                  </div>

                  <div className="pt-4 flex items-center justify-between mt-auto">
                    <span className="px-3 py-1 bg-black/[0.03] rounded-full text-[10px] font-mono font-bold uppercase tracking-widest text-black/40">
                      {agent.role}
                    </span>
                    <button
                      onClick={() => {
                        const newSessionId = Math.random().toString(36).substring(2, 15);
                        router.push(`/home/${newSessionId}?agent_id=${agent.id}`);
                      }}
                      className="text-sm font-bold text-black/80 hover:text-black hover:translate-x-1 transition-all flex items-center gap-2"
                    >
                      Deploy Agent <span>→</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {agents.length === 0 && !loading && (
          <div className="py-20 text-center space-y-4">
            <span className="text-6xl grayscale"></span>
            <h3 className="section-heading text-black/20">No agents yet. Your first specialization awaits.</h3>
          </div>
        )}
      </div>

      <AgentCreatorModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreated={fetchAgents}
        initialData={selectedAgent}
      />
    </div>
  );
}
