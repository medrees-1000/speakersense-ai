"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { CoachingEvent, LiveTick, SessionSummary } from "@/types/coaching";

function defaultWsUrl(): string {
  if (typeof process !== "undefined" && process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const isLocal =
      window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1" ||
      window.location.hostname === "::1";
    const host = isLocal
      ? `${window.location.hostname}:8080`
      : window.location.host;
    return `${proto}//${host}/ws/stream`;
  }
  return "ws://localhost:8080/ws/stream";
}

export interface UsePostureSocketOptions {
  onLive?: (tick: LiveTick) => void;
  onSummary?: (summary: SessionSummary) => void;
  onError?: (message: string) => void;
}

export function usePostureSocket(options: UsePostureSocketOptions = {}) {
  const wsRef = useRef<WebSocket | null>(null);
  const optionsRef = useRef(options);
  const [isConnected, setIsConnected] = useState(false);
  const audioCtxRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  const initAudioContext = useCallback(() => {
    if (!audioCtxRef.current) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      audioCtxRef.current = new AudioCtx({ sampleRate: 24000 });
    }
    if (audioCtxRef.current.state === "suspended") {
      audioCtxRef.current.resume();
    }
  }, []);

  const playPcmChunk = useCallback((base64Data: string) => {
    try {
      initAudioContext();
      const ctx = audioCtxRef.current;
      if (!ctx) return;

      const binaryStr = atob(base64Data);
      const len = binaryStr.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryStr.charCodeAt(i);
      }
      const int16Array = new Int16Array(bytes.buffer);
      const float32Array = new Float32Array(int16Array.length);
      for (let i = 0; i < int16Array.length; i++) {
        float32Array[i] = int16Array[i] / 32768.0;
      }

      const audioBuffer = ctx.createBuffer(1, float32Array.length, 24000);
      audioBuffer.getChannelData(0).set(float32Array);

      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);
      source.start();
    } catch {
      // ignore audio playback glitches
    }
  }, [initAudioContext]);

  const disconnect = useCallback(() => {
    const ws = wsRef.current;
    wsRef.current = null;
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      ws.close();
    }
    setIsConnected(false);
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    disconnect();
    initAudioContext();
    const ws = new WebSocket(defaultWsUrl());
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => {
      setIsConnected(false);
      if (wsRef.current === ws) wsRef.current = null;
    };
    ws.onerror = () => {
      optionsRef.current.onError?.(
        `WebSocket connection failed (${ws.url}). Check backend running on port 8080.`
      );
    };
    ws.onmessage = (event) => {
      try {
        const raw = JSON.parse(event.data);

        // Native Gemini audio payload handling
        if (raw.inlineData && raw.inlineData.mimeType?.startsWith("audio/pcm")) {
          playPcmChunk(raw.inlineData.data);
        }

        const parts = raw.serverContent?.modelTurn?.parts;
        if (parts && Array.isArray(parts)) {
          for (const part of parts) {
            if (part.inlineData && part.inlineData.mimeType?.startsWith("audio/pcm")) {
              playPcmChunk(part.inlineData.data);
            }
          }
        }

        if (raw.type === "audio" && raw.data) {
          playPcmChunk(raw.data);
        }

        // Live and Summary coaching events
        const data = raw as CoachingEvent | { type: "error"; message: string };
        if (data.type === "live") {
          optionsRef.current.onLive?.(data);
        } else if (data.type === "summary") {
          optionsRef.current.onSummary?.(data);
        } else if (data.type === "error") {
          optionsRef.current.onError?.(data.message);
        }
      } catch {
        // ignore malformed payloads
      }
    };
  }, [disconnect, initAudioContext, playPcmChunk]);

  const sendFrame = useCallback((base64Jpeg: string) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ type: "video_frame", data: base64Jpeg }));
  }, []);

  const endSession = useCallback(() => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ type: "session_end" }));
  }, []);

  useEffect(() => () => disconnect(), [disconnect]);

  return { isConnected, connect, disconnect, sendFrame, endSession };
}