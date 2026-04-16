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
  icon: string;
  created_at: string;
}

export default function AgentStudio() {
  const { user } = useAuth();
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

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

  const deleteAgent = async (id: string) => {
    if (!confirm("Are you sure you want to delete this agent?")) return;
    try {
      await fetch(`http://127.0.0.1:8000/api/agents/${id}`, { method: "DELETE" });
      fetchAgents();
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  return (
    <div className="flex-1 h-screen overflow-y-auto bg-[#fdfcf9] p-8 lg:p-12">
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Header */}
        <div className="flex items-end justify-between border-b border-black/[0.05] pb-8">
          <div className="space-y-2">
            <h1 className="display-hero !text-6xl tracking-tighter">Agent Studio</h1>
            <p className="body-standard max-w-md">Design and deploy specialized autonomous agents tailored to your business needs.</p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
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
                className="group relative bg-white border border-black/[0.03] rounded-[40px] p-8 shadow-xl shadow-black/[0.02] hover:shadow-2xl hover:shadow-black/[0.05] transition-all duration-500 hover:-translate-y-1"
              >
                <div className="flex flex-col h-full space-y-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="section-heading !text-3xl tracking-tight">{agent.name}</h3>
                    </div>
                    <button 
                      onClick={() => deleteAgent(agent.id)}
                      className="opacity-0 group-hover:opacity-40 hover:!opacity-100 p-2 text-black transition-opacity"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>

                  <div className="pt-4 flex items-center justify-between">
                    <span className="px-3 py-1 bg-black/[0.03] rounded-full text-[10px] font-mono font-bold uppercase tracking-widest text-black/40">
                      {agent.role}
                    </span>
                    <button
                      onClick={() => router.push(`/home?agent_id=${agent.id}`)}
                      className="text-sm font-medium text-black/60 hover:text-black hover:translate-x-1 transition-all flex items-center gap-2"
                    >
                      Deploy <span>→</span>
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
      />
    </div>
  );
}
