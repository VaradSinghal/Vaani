"use client";

import { useState, useRef, useCallback } from "react";

export interface VoiceAgentOptions {
  onUserTranscript?: (text: string) => void;
  onAgentTranscript?: (text: string) => void;
  onStatusChange?: (status: string) => void;
}

export function useVoiceAgent(options?: VoiceAgentOptions) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcripts, setTranscripts] = useState<string[]>([]);
  const [status, setStatus] = useState<"idle" | "listening" | "processing" | "thinking" | "speaking">("idle");

  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | ScriptProcessorNode | null>(null);
  const recordingContextRef = useRef<AudioContext | null>(null);

  // Separate playback context — never share with recording
  const playbackContextRef = useRef<AudioContext | null>(null);

  // Audio playback queue
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const isPlayingRef = useRef(false);

  // Refs for callbacks to avoid stale closures
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const getPlaybackContext = useCallback(() => {
    if (!playbackContextRef.current || playbackContextRef.current.state === "closed") {
      playbackContextRef.current = new AudioContext();
    }
    return playbackContextRef.current;
  }, []);

  const playNextChunk = useCallback(async () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      return;
    }

    isPlayingRef.current = true;
    const chunk = audioQueueRef.current.shift()!;

    try {
      const ctx = getPlaybackContext();
      if (ctx.state === "suspended") {
        await ctx.resume();
      }
      const buffer = await ctx.decodeAudioData(chunk);
      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);
      source.onended = () => playNextChunk();
      source.start();
    } catch (e) {
      console.error("Playback error:", e);
      // Skip this chunk and try the next
      playNextChunk();
    }
  }, [getPlaybackContext]);

  const enqueueAudio = useCallback((arrayBuffer: ArrayBuffer) => {
    audioQueueRef.current.push(arrayBuffer);
    if (!isPlayingRef.current) {
      playNextChunk();
    }
  }, [playNextChunk]);

  const connectWebSocket = useCallback((): Promise<WebSocket> => {
    return new Promise((resolve, reject) => {
      // Clean up any existing connection
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.onmessage = null;
        if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
          wsRef.current.close();
        }
        wsRef.current = null;
      }

      const ws = new WebSocket("ws://localhost:8000/voice-agent");
      wsRef.current = ws;

      ws.binaryType = "arraybuffer";

      ws.onopen = () => {
        console.log("WS: Connected to backend");
        resolve(ws);
      };

      ws.onerror = (err) => {
        console.error("WS: Connection error", err);
        reject(new Error("WebSocket connection failed"));
      };

      ws.onmessage = (event) => {
        if (typeof event.data === "string") {
          try {
            const msg = JSON.parse(event.data);
            
            if (msg.type === "transcript") {
              if (msg.is_final) {
                setTranscripts(prev => [...prev, `User: ${msg.text}`]);
                optionsRef.current?.onUserTranscript?.(msg.text);
              }
            } else if (msg.type === "agent_transcript") {
              setTranscripts(prev => [...prev, `Agent: ${msg.text}`]);
              optionsRef.current?.onAgentTranscript?.(msg.text);
            } else if (msg.type === "status") {
              setStatus(msg.status);
              optionsRef.current?.onStatusChange?.(msg.status);
            } else if (msg.type === "response_end") {
              setStatus("idle");
            }
          } catch (e) {
            console.error("WS: Failed to parse message", e);
          }
        } else if (event.data instanceof ArrayBuffer) {
          // Binary audio data from TTS
          setStatus("speaking");
          enqueueAudio(event.data);
        }
      };

      ws.onclose = () => {
        console.log("WS: Disconnected");
        wsRef.current = null;
        // NO auto-reconnect — connection is tied to recording lifecycle
      };
    });
  }, [enqueueAudio]);

  const startRecording = useCallback(async () => {
    try {
      // 1. Connect WebSocket first
      const ws = await connectWebSocket();

      // 2. Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        }
      });
      streamRef.current = stream;

      // 3. Create recording AudioContext
      const audioContext = new AudioContext({ sampleRate: 16000 });
      recordingContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      workletNodeRef.current = processor;

      processor.onaudioprocess = (e) => {
        if (ws.readyState !== WebSocket.OPEN) return;

        const inputData = e.inputBuffer.getChannelData(0);
        // Convert Float32 to Int16 PCM
        const pcmData = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]));
          pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        ws.send(pcmData.buffer);
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      setIsRecording(true);
      setStatus("listening");
      console.log("WS: Recording started");

    } catch (err) {
      console.error("Failed to start recording:", err);
      setStatus("idle");
    }
  }, [connectWebSocket]);

  const stopRecording = useCallback(() => {
    console.log("WS: Stopping recording");

    // Stop the audio processor
    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect();
      workletNodeRef.current = null;
    }

    // Stop microphone tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    // Close recording AudioContext
    if (recordingContextRef.current) {
      recordingContextRef.current.close().catch(() => {});
      recordingContextRef.current = null;
    }

    // Send end-of-speech signal (triggers backend processing)
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "eos" }));
    }

    setIsRecording(false);
    setStatus("processing");
  }, []);

  return {
    isRecording,
    transcripts,
    status,
    startRecording,
    stopRecording
  };
}
