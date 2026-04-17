"use client";

import { useState, useEffect } from "react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
  initialData?: any;
}

const TEMPLATES = [
  {
    "name": "Sales Pitcher",
    "role": "sales",
    "description": "Expert in SaaS product pitching and objection handling.",
    "instructions": "You are Roopa, a customer support agent at QuickKart, an e-commerce platform for electronics and home appliances. You handle order tracking, returns, refunds, and product inquiries. Be warm and solution-oriented. Acknowledge frustration before solving problems. Keep responses under 3 sentences. For refunds, explain the 5-7 business day timeline. For replacements, confirm the delivery address before proceeding. If a customer is angry, apologize sincerely and offer a concrete next step. Never argue or make excuses. When a customer asks about an order, ask for their order ID if they haven't provided one. Accept any order ID they give and simulate looking it up - create a realistic status like \"out for delivery\", \"shipped\", or \"processing\" based on the conversation flow.",
    "voice_id": "amrit"
  },
  {
    "name": "Medical Assistant",
    "role": "healthcare",
    "description": "Precision-focused coordinator for patient queries and clinical notes.",
    "instructions": "You are Ashutosh, the receptionist at HealthFirst Multi-Specialty Clinic in Bangalore. You schedule appointments for general physicians, dermatologists, and orthopedic specialists. Clinic hours are 9 AM to 8 PM, Monday to Saturday. Ask for the patient's name, preferred doctor or specialty, and convenient time slot. Confirm the appointment details before ending the call. If the requested slot is unavailable, offer the next two available options. For emergencies, direct patients to the 24/7 helpline. Keep the tone professional yet caring. Remind patients to bring their previous prescriptions and arrive 15 minutes early.",
    "voice_id": "pavithra"
  },
  {
    name: "Support Desk",
    role: "support",
    description: "Empathetic problem-solver for technical and billing issues.",
    instructions: "You are a technical support agent. You help users troubleshoot issues with a calm, empathetic tone. Guide them step-by-step and aim for single-touch resolution.",
    voice_id: "meera"
  }
];

const VOICES = [
  { id: "anushka", name: "Anushka", style: "Professional", gender: "F" },
  { id: "meera", name: "Meera", style: "Warm", gender: "F" },
  { id: "pavithra", name: "Pavithra", style: "Formal", gender: "F" },
  { id: "amrit", name: "Amrit", style: "Authoritative", gender: "M" },
  { id: "vatsal", name: "Vatsal", style: "Friendly", gender: "M" },
  { id: "kumar", name: "Kumar", style: "Mature", gender: "M" }
];

export function AgentCreatorModal({ isOpen, onClose, onCreated, initialData }: Props) {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    system_instructions: "",
    role: "general",
    tools_enabled: ["LIVE_READ"] as string[],
    voice_id: "anushka"
  });
  const [loading, setLoading] = useState(false);

  // Sync initialData for editing
  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || "",
        description: initialData.description || "",
        system_instructions: initialData.system_instructions || "",
        role: initialData.role || "general",
        tools_enabled: initialData.tools_enabled ?? ["LIVE_READ"],
        voice_id: initialData.voice_id || "anushka"
      });
    } else {
      setFormData({
        name: "",
        description: "",
        system_instructions: "",
        role: "general",
        tools_enabled: ["LIVE_READ"],
        voice_id: "anushka"
      });
    }
  }, [initialData, isOpen]);

  const applyTemplate = (tpl: any) => {
    setFormData({
      ...formData,
      name: tpl.name,
      description: tpl.description,
      system_instructions: tpl.instructions,
      role: tpl.role,
      tools_enabled: ["LIVE_READ"],
      voice_id: tpl.voice_id || "anushka"
    });
  };

  const handleAudition = async (voiceId: string) => {
    try {
      const sampleText = "Hello, I am your specialized Vaani agent. I'm ready to assist you with precision and expertise.";
      const res = await fetch("http://127.0.0.1:8000/api/voices/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voice_id: voiceId, text: sampleText })
      });
      const data = await res.json();
      if (data.audio) {
        const audio = new Audio(`data:audio/wav;base64,${data.audio}`);
        audio.play();
      }
    } catch (err) {
      console.error("Audition failed:", err);
    }
  };

  const toggleTool = (toolId: string) => {
    const current = [...formData.tools_enabled];
    if (current.includes(toolId)) {
      setFormData({ ...formData, tools_enabled: current.filter(t => t !== toolId) });
    } else {
      setFormData({ ...formData, tools_enabled: [...current, toolId] });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const url = initialData
        ? `http://127.0.0.1:8000/api/agents/${initialData.id}`
        : "http://127.0.0.1:8000/api/agents";

      const res = await fetch(url, {
        method: initialData ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        onCreated();
        onClose();
      }
    } catch (err) {
      console.error("Failed to save agent:", err);
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
                <h2 className="section-heading !text-3xl tracking-tight">
                  {initialData ? "Configure Agent" : "Create Agent"}
                </h2>
                <p className="text-sm text-black/40">
                  {initialData ? "Update permissions and expert logic." : "Define a persona and specialized knowledge profile."}
                </p>
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

              <div className="space-y-3">
                <label className="text-[11px] font-mono font-bold uppercase tracking-wider text-black/40">Vocal Persona & Voice</label>
                <div className="grid grid-cols-3 gap-2">
                  {VOICES.map(voice => (
                    <button
                      key={voice.id}
                      type="button"
                      onClick={() => setFormData({ ...formData, voice_id: voice.id })}
                      className={`relative flex flex-col p-3 rounded-2xl border transition-all text-left ${formData.voice_id === voice.id
                        ? "bg-black text-white border-black"
                        : "bg-white text-black/60 border-black/[0.05] hover:border-black/20"
                        }`}
                    >
                      <div className="text-xs font-bold">{voice.name}</div>
                      <div className="text-[9px] uppercase tracking-tighter opacity-40">{voice.style}</div>

                      <div
                        onClick={(e) => { e.stopPropagation(); handleAudition(voice.id); }}
                        className="absolute bottom-2 right-2 p-1.5 rounded-full bg-black/5 hover:bg-black/10 transition-colors cursor-pointer group-hover:bg-black/20"
                        title="Audition Voice"
                      >
                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z" />
                        </svg>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-[11px] font-mono font-bold uppercase tracking-wider text-black/40">Capabilities & Toolset</label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { id: "GMAIL", name: "Gmail" },
                    { id: "SLACK", name: "Slack" },
                    { id: "NOTION", name: "Notion" },
                    { id: "CALENDAR", name: "Calendar" },
                    { id: "LIVE_READ", name: "Doc Intelligence" }
                  ].map(tool => (
                    <button
                      key={tool.id}
                      type="button"
                      onClick={() => toggleTool(tool.id)}
                      className={`flex items-center gap-3 p-3 rounded-2xl border transition-all ${formData.tools_enabled.includes(tool.id)
                        ? "bg-black text-white border-black"
                        : "bg-white text-black/60 border-black/[0.05] hover:border-black/20"
                        }`}
                    >
                      <span className="text-xs font-semibold">{tool.name}</span>
                      {formData.tools_enabled.includes(tool.id) && (
                        <div className="ml-auto w-1.5 h-1.5 rounded-full bg-cur-orange shadow-[0_0_8px_rgba(245,78,0,0.6)]" />
                      )}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 bg-[#2d2c25] text-white rounded-full font-bold hover:scale-[1.02] transition-all active:scale-95 disabled:opacity-50 shadow-xl shadow-black/10"
              >
                {loading ? "Syncing..." : initialData ? "Update Configuration" : "Create Specialized Agent"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
