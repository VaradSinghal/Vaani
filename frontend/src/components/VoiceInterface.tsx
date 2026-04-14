"use client";

import { useVoiceAgent } from "../hooks/useVoiceAgent";

export function VoiceInterface() {
  const { isRecording, status, transcripts, startRecording, stopRecording } = useVoiceAgent();

  return (
    <div id="voice-agent" className="py-24 max-w-[1200px] mx-auto px-6">
      <div className="cursor-card overflow-hidden bg-cur-surface-100 shadow-2xl">
        <div className="flex flex-col lg:flex-row min-h-[600px]">
          {/* Interaction Side */}
          <div className="flex-[3] p-16 flex flex-col items-center justify-center border-b lg:border-b-0 lg:border-r border-border-primary bg-cur-cream">
            <div className="relative mb-12">
              <div className={`absolute inset-0 rounded-full border border-cursor-orange transition-all duration-700 ${isRecording ? "scale-150 opacity-0 animate-ping" : "scale-100 opacity-0"}`}></div>
              
              <button 
                onClick={isRecording ? stopRecording : startRecording}
                className={`group relative w-40 h-40 rounded-full flex items-center justify-center transition-all ${isRecording ? "bg-cur-surface-300 shadow-inner" : "bg-cur-surface-300 border border-border-medium hover:border-border-strong shadow-lg"}`}
              >
                {isRecording ? (
                  <div className="w-10 h-10 bg-cur-error rounded-sm animate-pulse"></div>
                ) : (
                  <div className="flex flex-col items-center">
                    <svg className="w-16 h-16 text-cursor-dark opacity-80 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                  </div>
                )}
              </button>
            </div>

            <div className="text-center">
              <h2 className="section-heading !text-[28px] mb-3">
                {status === "idle" ? "Begin Conversation" : 
                 status === "listening" ? "Listening..." : "Agent Active"}
              </h2>
              <p className="body-standard !text-[16px] max-w-[320px] mx-auto">
                {isRecording ? "I'm capturing your speech for real-time translation." : "Click the microphone to start a multilingual session."}
              </p>
            </div>
          </div>

          {/* Timeline & Feedback Side */}
          <div className="flex-[4] p-16 flex flex-col">
            <div className="flex items-center justify-between mb-12">
              <span className="font-mono text-[11px] uppercase tracking-wider text-border-strong opacity-60">AI Timeline</span>
              <div className="flex gap-1.5">
                <div className={`w-2 h-2 rounded-full ${status === 'listening' ? "bg-cur-orange" : "bg-border-primary"}`}></div>
                <div className={`w-2 h-2 rounded-full ${status === 'processing' ? "bg-time-thinking animate-pulse" : "bg-border-primary"}`}></div>
                <div className={`w-2 h-2 rounded-full ${status === 'speaking' ? "bg-time-edit animate-pulse" : "bg-border-primary"}`}></div>
              </div>
            </div>

            {/* AI Timeline metaphor */}
            <div className="flex-1 space-y-12">
              <div className="relative">
                <div className="absolute left-[7px] top-6 bottom-[-48px] w-[2px] bg-border-primary"></div>
                
                <div className="space-y-12">
                  <TimelineStep 
                    active={status === 'listening'} 
                    done={transcripts.length > 0} 
                    color="#9fc9a2" 
                    label="Grep" 
                    desc="Listening and segmenting Indian dialect tokens" 
                  />
                  <TimelineStep 
                    active={status === 'processing'} 
                    done={status === 'speaking'} 
                    color="#dfa88f" 
                    label="Think" 
                    desc="Contextual reasoning via Sarvam-105b Model" 
                  />
                  <TimelineStep 
                    active={status === 'speaking'} 
                    color="#c0a8dd" 
                    label="Edit" 
                    desc="Synthesizing high-fidelity Bulbul v3 voice" 
                  />
                </div>
              </div>

              {/* Latest Transcription Clip */}
              <div className="mt-16 pt-12 border-t border-border-primary">
                <div className="font-mono text-[11px] mb-6 text-border-strong opacity-60 uppercase">Latest Context</div>
                <div className="space-y-4">
                  {transcripts.slice(-2).map((t, i) => (
                    <div key={i} className="flex gap-4 items-start animate-cursor">
                      <div className={`font-mono text-[12px] mt-1 ${t.startsWith('User:') ? "text-cur-orange" : "text-time-edit"}`}>
                        {t.split(':')[0]}
                      </div>
                      <div className="font-editorial text-[17px] leading-relaxed text-cursor-dark font-medium">
                        {t.split(':')[1]}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TimelineStep({ active, done, color, label, desc }: { active?: boolean, done?: boolean, color: string, label: string, desc: string }) {
  return (
    <div className={`flex gap-6 transition-opacity duration-500 ${!active && !done ? "opacity-30" : "opacity-100"}`}>
      <div className="relative z-10 w-4 h-4 rounded-full border-2 border-cur-cream bg-cur-dark flex items-center justify-center mt-1.5" style={{ backgroundColor: done ? color : active ? color : undefined }}>
        {done && (
          <svg className="w-2.5 h-2.5 text-cur-cream" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        )}
      </div>
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="font-mono text-[12px] font-bold" style={{ color: active || done ? color : undefined }}>{label}</span>
          {active && <span className="w-1 h-1 rounded-full bg-cur-orange animate-ping"></span>}
        </div>
        <p className="font-sans text-[14px] text-border-strong leading-tight">{desc}</p>
      </div>
    </div>
  );
}
