"use client";

import { useVoiceAgent } from "../hooks/useVoiceAgent";
import { useChat } from "../hooks/useChat";
import { useEffect, useRef } from "react";

interface ChatInterfaceProps {
  sessionId: string;
}

export function ChatInterface({ sessionId }: ChatInterfaceProps) {
  const { addMessage, messages, loading: chatLoading } = useChat(sessionId);
  
  const { isRecording, status, startRecording, stopRecording } = useVoiceAgent({
    onUserTranscript: (text) => addMessage(sessionId, "User", text),
    onAgentTranscript: (text) => addMessage(sessionId, "Agent", text),
  });

  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, status]);

  return (
    <div className="flex flex-col h-full bg-cur-cream relative overflow-hidden">
      {/* Session Header */}
      <header className="flex-none px-6 h-14 border-b border-border-primary flex items-center justify-between bg-cur-cream/80 backdrop-blur-md z-10">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-cur-success animate-pulse" />
          <span className="font-mono text-[11px] uppercase tracking-widest text-border-strong">
            Sarvam-105b Hybrid Mode
          </span>
        </div>
        <div className="text-[12px] font-medium text-border-strong opacity-60">
          Latency: ~740ms
        </div>
      </header>

      {/* Messages Area - Slim Centered */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto scrollbar-hide"
      >
        <div className="max-w-2xl mx-auto px-6 py-12 space-y-10">
          {chatLoading ? (
            <div className="flex justify-center py-20">
               <div className="w-6 h-6 rounded-full border-2 border-cur-orange border-t-transparent animate-spin" />
            </div>
          ) : messages.length === 0 ? (
            <div className="py-20 flex flex-col items-center justify-center text-center space-y-6 opacity-40 select-none">
              <div className="w-16 h-16 bg-cur-surface-300 rounded-2xl flex items-center justify-center">
                <svg className="w-8 h-8 text-cursor-dark" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="section-heading !text-2xl">Vaani is ready.</h3>
              <p className="body-standard max-w-xs leading-relaxed italic">
                “Language is the architecture of thought.”
              </p>
            </div>
          ) : (
            messages.map((m) => (
              <div 
                key={m.id} 
                className={`flex gap-6 animate-cursor ${m.role === "User" ? "justify-end" : "justify-start"}`}
              >
                <div className={`max-w-[85%] rounded-2xl px-6 py-4 shadow-sm ${
                  m.role === "User" 
                  ? "bg-cursor-dark text-cur-cream rounded-tr-none" 
                  : "bg-cur-surface-300 border border-border-primary text-cursor-dark rounded-tl-none"
                }`}>
                  <p className="body-serif !text-[17.5px] leading-relaxed">
                    {m.text}
                  </p>
                </div>
              </div>
            ))
          )}
          
          {/* Real-time Status Indicator */}
          {status !== "idle" && (
            <div className="flex justify-start animate-cursor">
              <div className="bg-cur-surface-100 border border-border-primary rounded-2xl px-4 py-2 flex items-center gap-3">
                <div className={`w-1.5 h-1.5 rounded-full ${
                  status === "listening" ? "bg-cur-orange" : 
                  status === "processing" ? "bg-time-thinking" : "bg-time-edit"
                } animate-ping`} />
                <span className="font-mono text-[11px] uppercase tracking-widest text-border-strong">
                  {status === "listening" ? "Listening" : 
                   status === "processing" ? "Thinking" : "Speaking"}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input Area - Floats at the bottom */}
      <div className="flex-none p-8 bg-gradient-to-t from-cur-cream via-cur-cream/90 to-transparent">
        <div className="max-w-2xl mx-auto flex flex-col items-center">
          <div className="relative group">
            <div className={`absolute -inset-6 rounded-full border border-cur-orange/20 transition-all duration-700 ${isRecording ? "scale-150 opacity-0 animate-ping" : "scale-100 opacity-0"}`}></div>
            
            <button 
              onClick={isRecording ? stopRecording : startRecording}
              className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 ${
                isRecording 
                ? "bg-cur-error shadow-inner scale-95" 
                : "bg-cur-surface-300 border border-border-medium shadow-lg hover:shadow-xl hover:scale-105 active:scale-95"
              }`}
            >
              {isRecording ? (
                <div className="w-6 h-6 bg-white rounded-sm"></div>
              ) : (
                <svg className="w-8 h-8 text-cursor-dark" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              )}
            </button>
          </div>
          
          <div className="mt-6 text-center">
            <span className="font-mono text-[11px] uppercase tracking-widest text-border-strong opacity-40">
              {isRecording ? "I'm listening..." : "Tap to Speak"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
