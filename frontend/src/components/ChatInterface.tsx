"use client";

import { useVoiceAgent } from "../hooks/useVoiceAgent";
import { useChat } from "../hooks/useChat";
import { useSearchParams } from "next/navigation";
import { useDocuments } from "../hooks/useDocuments";
import { useAuth } from "../context/AuthContext";
import { useEffect, useRef, useState } from "react";

interface ChatInterfaceProps {
  sessionId: string;
}

export function ChatInterface({ sessionId }: ChatInterfaceProps) {
  const { user } = useAuth();
  const { addMessage, messages, loading: chatLoading } = useChat(sessionId);
  const { documents, uploading, uploadProgress, uploadDocument } = useDocuments();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const searchParams = useSearchParams();
  const agentId = searchParams.get("agent_id") || undefined;
  
  const [activeSources, setActiveSources] = useState<string[]>([]);
  const [activeAgent, setActiveAgent] = useState<any>(null);

  useEffect(() => {
    if (agentId) {
      fetch(`http://127.0.0.1:8000/api/agents`).then(res => res.json()).then(data => {
        const agent = data.agents.find((a: any) => a.id === agentId);
        if (agent) setActiveAgent(agent);
      });
    }
  }, [agentId]);

  const { isRecording, status, startRecording, stopRecording } = useVoiceAgent({
    uid: user?.uid,
    agentId: agentId,
    onUserTranscript: (text) => {
      addMessage(sessionId, "User", text);
      setActiveSources([]);
    },
    onAgentTranscript: (text) => addMessage(sessionId, "Agent", text, activeSources),
    onAttribution: (sources) => setActiveSources(sources),
  });

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, status]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await uploadDocument(file, "en-IN", user?.uid || "anonymous");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className={`flex flex-col h-full bg-[#fdfcf9] relative overflow-hidden font-sans transition-colors duration-1000 ${activeAgent ? 'bg-[#f7f7f4]' : ''}`}>
      {/* Studio Space Background Layer */}
      {activeAgent && (
        <div className="absolute inset-0 studio-grid animate-in fade-in duration-1000" />
      )}

      {/* Viewport Focus Frame */}
      {activeAgent && (
        <div className="absolute inset-4 studio-inset-frame z-10 pointer-events-none border border-black/[0.02]" />
      )}

      {/* Premium Header */}
      <header className="flex-none px-8 h-16 border-b border-black/[0.03] flex items-center justify-between bg-white/40 backdrop-blur-xl z-20">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className={`w-2.5 h-2.5 rounded-full ${activeAgent ? 'bg-cur-orange shadow-[0_0_12px_rgba(245,78,0,0.3)]' : 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]'} transition-all`} />
            <div className="flex flex-col -space-y-0.5">
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-black/40 font-bold">
                {activeAgent ? 'Expert Intelligence Space' : 'Hybrid Reasoning'}
              </span>
              <span className="text-sm font-semibold text-black/80">
                {activeAgent ? activeAgent.name : 'Vaani Core'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="h-4 w-px bg-black/5" />
          <span className="text-[11px] font-mono text-black/30">L_670ms</span>
        </div>
      </header>

      {/* Messages Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto scrollbar-hide px-6"
      >
        <div className="max-w-2xl mx-auto py-12 space-y-12">
          {chatLoading ? (
            <div className="flex justify-center py-20">
              <div className="w-1.5 h-1.5 rounded-full bg-black/10 animate-bounce [animation-delay:-0.3s]" />
              <div className="w-1.5 h-1.5 rounded-full bg-black/10 animate-bounce [animation-delay:-0.15s] mx-1" />
              <div className="w-1.5 h-1.5 rounded-full bg-black/10 animate-bounce" />
            </div>
          ) : messages.length === 0 ? (
            <div className="py-20 flex flex-col items-center justify-center text-center space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
              <div className="w-24 h-24 bg-gradient-to-br from-[#f8f7f2] to-[#f0efe9] rounded-[40px] shadow-2xl shadow-black/[0.02] flex items-center justify-center rotate-3 scale-110">
                <span className="text-4xl">🎙️</span>
              </div>
              <div className="space-y-3">
                <h3 className="section-heading !text-4xl tracking-tight text-black/80">Vaani</h3>
              </div>
            </div>
          ) : (
            messages.map((m, idx) => (
              <div
                key={m.id}
                className={`flex flex-col gap-2 animate-in fade-in slide-in-from-bottom-2 duration-500 fill-mode-both`}
                style={{ animationDelay: `${idx * 50}ms` }}
              >
                <div className={`flex ${m.role === "User" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[88%] px-7 py-5 shadow-2xl shadow-black/[0.02] ${m.role === "User"
                      ? "bg-[#2d2c25] text-[#fdfcf9] rounded-[28px] rounded-tr-none"
                      : "bg-white border border-black/[0.03] text-black/90 rounded-[28px] rounded-tl-none font-serif text-[19px] leading-[1.6]"
                    }`}>
                    {m.text}

                    {/* Attribution Badges */}
                    {m.role === "Agent" && m.sources && m.sources.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-black/[0.03] flex flex-wrap gap-2">
                        {m.sources.map((src, i) => (
                          <div key={i} className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-black/[0.02] border border-black/[0.03] group cursor-default hover:bg-black/[0.04] transition-colors">
                            <span className="text-[10px]">📄</span>
                            <span className="font-mono text-[9px] text-black/40 uppercase tracking-widest font-bold">{src}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}

          {/* Real-time Status Waveform Replacement */}
          {status !== "idle" && (
            <div className="flex justify-start animate-in fade-in zoom-in duration-300">
              <div className="bg-white/80 backdrop-blur-md border border-black/[0.03] rounded-full px-5 py-2.5 flex items-center gap-4 shadow-xl shadow-black/[0.02]">
                <div className="flex gap-1 items-center h-4">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className={`w-0.5 rounded-full bg-cur-orange animate-pulse`}
                      style={{
                        height: `${Math.random() * 100}%`,
                        animationDuration: `${0.5 + Math.random()}s`
                      }}
                    />
                  ))}
                </div>
                <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-black/50 font-bold">
                  {status === "listening" ? "Listening" :
                    status === "thinking" ? "Thinking" :
                      status === "speaking" ? "Speaking" :
                        status.replace("_", " ")}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Floating Interaction HUD */}
      <div className={`flex-none p-10 bg-gradient-to-t from-[#fdfcf9] via-[#fdfcf9]/80 to-transparent relative z-30 transition-all duration-500 ${activeAgent ? 'px-14 pb-14' : ''}`}>
        <div className="max-w-2xl mx-auto">
          <div className={`flex items-center justify-between gap-8 backdrop-blur-3xl border border-black/[0.03] rounded-[40px] p-2 pl-3 shadow-2xl transition-all duration-500 ${activeAgent ? 'hud-studio shadow-black/[0.08] scale-[1.02]' : 'bg-white/40 shadow-black/[0.05]'}`}>

            {/* Left: Quick Actions */}
            <div className="flex items-center gap-2">
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileUpload}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-12 h-12 rounded-full flex items-center justify-center hover:bg-black/5 transition-all text-black/40 hover:text-black hover:scale-105 active:scale-95"
                title="Attach Document"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
              </button>
            </div>

            {/* Middle: Recording Interaction */}
            <div className="flex items-center gap-4">
              <button
                onClick={isRecording ? stopRecording : startRecording}
                className={`group relative flex items-center justify-center transition-all duration-500 ${isRecording ? "w-40 bg-cur-error rounded-full" : "w-14 h-14 bg-[#2d2c25] rounded-full shadow-lg shadow-[#2d2c25]/20 hover:scale-105 active:scale-95"
                  } h-14 overflow-hidden`}
              >
                {isRecording ? (
                  <div className="flex items-center gap-3 px-6">
                    <div className="w-2.5 h-2.5 bg-white rounded-full animate-pulse" />
                    <span className="text-white text-[13px] font-medium uppercase tracking-widest">End Session</span>
                  </div>
                ) : (
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                )}
                {/* Visual Feedback Ring */}
                {!isRecording && (
                  <div className="absolute inset-0 border-2 border-white/0 group-hover:border-white/10 rounded-full transition-all duration-500 scale-125 group-hover:scale-100" />
                )}
              </button>
            </div>

            {/* Right: Library Context */}
            <div className="pr-2">
              <button
                onClick={() => window.location.href = '/home/documents'}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-black/5 hover:bg-black/10 transition-all group"
              >
                <span className="text-xs font-mono font-bold text-black/40 group-hover:text-black/60 tracking-wider uppercase">Library</span>
                <span className="text-sm">📚</span>
              </button>
            </div>
          </div>

          {uploadProgress && (
            <div className="absolute -top-12 left-1/2 -translate-x-1/2 animate-in fade-in slide-in-from-bottom-2">
              <div className="px-4 py-1.5 bg-emerald-50 border border-emerald-100 rounded-full flex items-center gap-2 shadow-sm">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span className="text-[11px] font-mono text-emerald-700 font-bold uppercase tracking-wider">{uploadProgress}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
