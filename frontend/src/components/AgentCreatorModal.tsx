"use client";

import { useState } from "react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

const TEMPLATES = [
  {
    name: "Sales Pitcher",
    role: "sales",
    description: "Expert in SaaS product pitching and objection handling.",
    instructions: "You are a high-energy Sales Executive. Your goal is to pitch Vaani as a revolutionary voice-first productivity platform. Focus on ROI, time-savings, and tech-forward aesthetics. Be persuasive but professional."
  },
  {
    name: "Medical Assistant",
    role: "healthcare",
    description: "Precision-focused coordinator for patient queries and clinical notes.",
    instructions: "You are a specialized Medical Assistant. You help healthcare professionals with patient data coordination, clinical note taking, and medical scheduling. Always prioritize data accuracy and HIPAA-compliant communication styles."
  },
  {
    name: "Support Desk",
    role: "support",
    description: "Empathetic problem-solver for technical and billing issues.",
    instructions: "You are a technical support agent. You help users troubleshoot issues with a calm, empathetic tone. Guide them step-by-step and aim for single-touch resolution."
  }
];

export function AgentCreatorModal({ isOpen, onClose, onCreated }: Props) {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    system_instructions: "",
    role: "general"
  });
  const [loading, setLoading] = useState(false);

  const applyTemplate = (tpl: typeof TEMPLATES[0]) => {
    setFormData({
      ...formData,
      name: tpl.name,
      description: tpl.description,
      system_instructions: tpl.instructions,
      role: tpl.role
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        onCreated();
        onClose();
      }
    } catch (err) {
      console.error("Failed to create agent:", err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
      <div className="bg-[#fdfcf9] w-full max-w-2xl rounded-[48px] overflow-hidden shadow-2xl animate-in zoom-in-95 duration-300">
        <div className="flex h-[600px]">
          {/* Sidebar: Templates */}
          <div className="w-1/3 bg-black/[0.02] p-8 border-r border-black/[0.05] space-y-6">
            <h4 className="font-mono text-[10px] uppercase tracking-widest text-black/40">Quick Templates</h4>
            <div className="space-y-3">
              {TEMPLATES.map((tpl) => (
                <button
                  key={tpl.name}
                  onClick={() => applyTemplate(tpl)}
                  className="w-full text-left p-4 rounded-3xl bg-white border border-black/[0.05] hover:border-black/20 hover:shadow-lg transition-all group"
                >
                  <div className="flex flex-col gap-1 min-w-0">
                    <div className="text-xs font-bold text-black/80 truncate">{tpl.name}</div>
                    <div className="text-[10px] text-black/40 truncate">{tpl.role}</div>
                  </div>
                </button>
              ))}
            </div>
            <p className="text-[11px] text-black/30 leading-relaxed italic">Select a template to pre-fill the form with expert system instructions.</p>
          </div>

          {/* Main Form */}
          <div className="flex-1 p-10 overflow-y-auto relative">
            <button onClick={onClose} className="absolute top-8 right-8 text-black/20 hover:text-black transition-colors">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-1">
                <h2 className="section-heading !text-3xl tracking-tight">Create Agent</h2>
                <p className="text-sm text-black/40">Define a persona and specialized knowledge profile.</p>
              </div>

              <div className="grid grid-cols-4 gap-4">
                <div className="col-span-3 space-y-1.5">
                  <label className="text-[11px] font-mono font-bold uppercase tracking-wider text-black/40">Name</label>
                  <input
                    required
                    value={formData.name}
                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                    className="w-full bg-white border border-black/[0.05] rounded-2xl px-4 py-3 text-sm focus:outline-none focus:border-black/20 transition-all"
                    placeholder="e.g. Sales Oracle"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-[11px] font-mono font-bold uppercase tracking-wider text-black/40">System Instructions</label>
                <textarea
                  required
                  value={formData.system_instructions}
                  onChange={e => setFormData({ ...formData, system_instructions: e.target.value })}
                  rows={6}
                  className="w-full bg-white border border-black/[0.05] rounded-3xl px-5 py-4 text-sm focus:outline-none focus:border-black/20 transition-all resize-none font-sans"
                  placeholder="Explain exactly how this agent should behave..."
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 bg-[#2d2c25] text-white rounded-full font-bold hover:scale-[1.02] transition-all active:scale-95 disabled:opacity-50 shadow-xl shadow-black/10"
              >
                {loading ? "Forging Agent..." : "Create Specialized Agent"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
