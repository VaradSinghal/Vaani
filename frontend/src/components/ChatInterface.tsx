"use client";

import { useVoiceAgent } from "../hooks/useVoiceAgent";
import { useEffect, useRef } from "react";

export function ChatInterface() {
  const { isRecording, status, transcripts, startRecording, stopRecording } = useVoiceAgent();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcripts]);

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-4xl mx-auto w-full bg-cur-cream animate-cursor">
      {/* Messages Area */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-6 py-8 space-y-8 scrollbar-hide"
      >
        {transcripts.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-6 opacity-40">
            <div className="w-16 h-16 bg-cur-surface-300 rounded-2xl flex items-center justify-center">
              <svg className="w-8 h-8 text-cursor-dark" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 className="section-heading !text-2xl">Vaani is ready.</h3>
            <p className="body-standard max-w-sm">Tap the microphone to start a natural conversation in your preferred language.</p>
          </div>
        ) : (
          transcripts.map((t, i) => {
            const [role, ...textParts] = t.split(": ");
            const isUser = role === "User";
            const text = textParts.join(": ");
            
            return (
              <div 
                key={i} 
                className={`flex ${isUser ? "justify-end" : "justify-start"} animate-cursor`}
              >
                <div className={`max-w-[80%] rounded-2xl px-6 py-4 shadow-sm ${
                  isUser 
                  ? "bg-cursor-dark text-cur-cream rounded-tr-none" 
                  : "bg-cur-surface-300 border border-border-primary text-cursor-dark rounded-tl-none"
                }`}>
                  <p className="body-serif !text-[17px] leading-relaxed">
                    {text}
                  </p>
                </div>
              </div>
            );
          })
        )}
        
        {/* Status Bubble */}
        {status !== "idle" && (
          <div className="flex justify-start animate-pulse">
            <div className="bg-cur-surface-100 border border-border-primary rounded-2xl px-4 py-2 flex items-center gap-2">
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

      {/* Input Area */}
      <div className="p-8 bg-gradient-to-t from-cur-cream via-cur-cream to-transparent">
        <div className="relative max-w-2xl mx-auto flex flex-col items-center">
          {/* Interaction Ring */}
          <div className="relative group">
            <div className={`absolute -inset-4 rounded-full border border-cur-orange/30 transition-all duration-700 ${isRecording ? "scale-150 opacity-0 animate-ping" : "scale-100 opacity-0"}`}></div>
            
            <button 
              onClick={isRecording ? stopRecording : startRecording}
              className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 ${
                isRecording 
                ? "bg-cur-error shadow-inner rotate-0" 
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
              {isRecording ? "Listening to your intent..." : "Click to Speak"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
