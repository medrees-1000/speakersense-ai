"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { CoachingEvent, LiveTick, SessionSummary } from "@/types/coaching";

function defaultWsUrl(): string {
  if (typeof process !== "undefined" && process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    return `${proto}://localhost:8000/ws/stream`;
  }
  return "ws://localhost:8000/ws/stream";
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

  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  const disconnect = useCallback(() => {
    const ws = wsRef.current;
    wsRef.current = null;
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      ws.close();
    }
    setIsConnected(false);
  }, []);

  const connect = useCallback(() => {
    disconnect();
    const ws = new WebSocket(defaultWsUrl());
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => {
      setIsConnected(false);
      if (wsRef.current === ws) wsRef.current = null;
    };
    ws.onerror = () => {
      optionsRef.current.onError?.("WebSocket connection failed. Is the backend running?");
    };
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as CoachingEvent | { type: "error"; message: string };
        if (data.type === "live") {
          optionsRef.current.onLive?.(data);
        } else if (data.type === "summary") {
          optionsRef.current.onSummary?.(data);
        } else if (data.type === "error") {
          optionsRef.current.onError?.(data.message);
        }
      } catch {
        // ignore malformed frames
      }
    };
  }, [disconnect]);

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
