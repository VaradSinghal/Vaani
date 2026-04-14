"use client";

import { useState, useEffect, useRef, useCallback } from "react";

export function useVoiceAgent() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcripts, setTranscripts] = useState<string[]>([]);
  const [status, setStatus] = useState<"idle" | "listening" | "processing" | "speaking">("idle");
  
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  
  // Playback queue
  const audioQueueRef = useRef<Uint8Array[]>([]);
  const isPlayingRef = useRef(false);

  const connect = useCallback(() => {
    const ws = new WebSocket("ws://localhost:8000/voice-agent");
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("Connected to backend");
    };

    ws.onmessage = async (event) => {
      if (typeof event.data === "string") {
        const msg = JSON.parse(event.data);
        if (msg.type === "transcript") {
           setTranscripts(prev => [...prev, `User: ${msg.text}`]);
        }
      } else {
        // Audio chunk (binary)
        const arrayBuffer = await event.data.arrayBuffer();
        audioQueueRef.current.push(new Uint8Array(arrayBuffer));
        if (!isPlayingRef.current) {
          playNextChunk();
        }
      }
    };

    ws.onclose = () => {
      console.log("Disconnected from backend");
      setTimeout(connect, 2000); // Reconnect
    };
  }, []);

  const playNextChunk = async () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      setStatus("idle");
      return;
    }

    isPlayingRef.current = true;
    setStatus("speaking");
    const chunk = audioQueueRef.current.shift()!;
    
    if (!audioContextRef.current) return;

    try {
      // Decode audio chunk (assuming MP3 or WAV from Bulbul v3)
      const buffer = await audioContextRef.current.decodeAudioData(chunk.buffer as ArrayBuffer);
      const source = audioContextRef.current.createBufferSource();
      source.buffer = buffer;
      source.connect(audioContextRef.current.destination);
      source.onended = () => playNextChunk();
      source.start();
    } catch (e) {
      console.error("Playback error:", e);
      playNextChunk();
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const audioContext = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = audioContext;
      
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        // Convert to Int16 PCM
        const pcmData = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
        }
        
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(pcmData.buffer);
        }
      };

      source.connect(processor);
      processor.connect(audioContext.destination);
      
      setIsRecording(true);
      setStatus("listening");
    } catch (err) {
       console.error("Could not start recording:", err);
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    setStatus("idle");
    
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "eos" }));
    }
  };

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return {
    isRecording,
    transcripts,
    status,
    startRecording,
    stopRecording
  };
}
