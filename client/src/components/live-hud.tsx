"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import WebcamFeed from "./webcam-feed";
import { useWebcam } from "@/hooks/use-webcam";
import { usePostureSocket } from "@/hooks/use-socket";
import {
  SUMMARY_STORAGE_KEY,
  type LiveTick,
  type SessionSummary,
} from "@/types/coaching";
import { Video, VideoOff, Loader2 } from "lucide-react";

function formatPosture(posture?: string): string {
  if (!posture) return "—";
  return posture.replace(/_/g, " ");
}

function speakCue(text: string) {
  if (typeof window === "undefined" || !window.speechSynthesis || !text.trim()) {
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text.trim());
  utterance.rate = 1.05;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
}

export default function LiveHUD() {
  const router = useRouter();
  const [isRecording, setIsRecording] = useState(false);
  const [ending, setEnding] = useState(false);
  const [tick, setTick] = useState<LiveTick | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const lastSpokenRef = useRef<{ cue: string; at: number }>({ cue: "", at: 0 });
  const gotSummaryRef = useRef(false);
  const endTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const disconnectRef = useRef<() => void>(() => {});

  const handleLive = useCallback((next: LiveTick) => {
    setTick(next);
    if (next.alert && next.spoken_cue) {
      const now = Date.now();
      const last = lastSpokenRef.current;
      if (next.spoken_cue !== last.cue || now - last.at > 6000) {
        speakCue(next.spoken_cue);
        lastSpokenRef.current = { cue: next.spoken_cue, at: now };
      }
    }
  }, []);

  const handleSummary = useCallback(
    (summary: SessionSummary) => {
      gotSummaryRef.current = true;
      if (endTimeoutRef.current) {
        clearTimeout(endTimeoutRef.current);
        endTimeoutRef.current = null;
      }
      try {
        sessionStorage.setItem(SUMMARY_STORAGE_KEY, JSON.stringify(summary));
      } catch {
        // ignore
      }
      setEnding(false);
      setIsRecording(false);
      disconnectRef.current();
      router.push("/summary");
    },
    [router]
  );

  const handleError = useCallback((message: string) => {
    setStatusMessage(message);
    setEnding(false);
  }, []);

  const { isConnected, connect, disconnect, sendFrame, endSession } =
    usePostureSocket({
      onLive: handleLive,
      onSummary: handleSummary,
      onError: handleError,
    });

  useEffect(() => {
    disconnectRef.current = disconnect;
  }, [disconnect]);

  const onFrame = useCallback(
    (base64Jpeg: string) => {
      if (isRecording && !ending) sendFrame(base64Jpeg);
    },
    [isRecording, ending, sendFrame]
  );

  const { attachVideo, error: cameraError } = useWebcam({
    active: isRecording,
    onFrame,
  });

  useEffect(() => {
    if (cameraError) setStatusMessage(cameraError);
  }, [cameraError]);

  useEffect(() => {
    return () => {
      if (endTimeoutRef.current) clearTimeout(endTimeoutRef.current);
    };
  }, []);

  const startSession = () => {
    gotSummaryRef.current = false;
    setTick(null);
    setStatusMessage(null);
    setEnding(false);
    lastSpokenRef.current = { cue: "", at: 0 };
    try {
      sessionStorage.removeItem(SUMMARY_STORAGE_KEY);
    } catch {
      // ignore
    }
    setIsRecording(true);
    connect();
  };

  const stopSession = () => {
    if (ending) return;
    setEnding(true);
    setStatusMessage("Generating your posture report…");
    endSession();
    endTimeoutRef.current = setTimeout(() => {
      endTimeoutRef.current = null;
      if (gotSummaryRef.current) return;
      setEnding(false);
      setIsRecording(false);
      disconnect();
      setStatusMessage("Session ended. Waiting for report timed out — try again.");
    }, 12000);
  };

  const postureLabel = tick?.posture
    ? `${formatPosture(tick.posture)}${tick.alert ? " · ALERT" : ""}`
    : isRecording
    ? "Analyzing..."
    : undefined;

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 backdrop-blur shadow-2xl max-w-4xl mx-auto">
      <WebcamFeed
        videoRef={attachVideo}
        isActive={isRecording}
        postureLabel={postureLabel}
        alerting={Boolean(tick?.alert)}
      />

      {statusMessage && (
        <p className="mt-4 text-center text-sm text-amber-300/90">{statusMessage}</p>
      )}

      <div className="flex items-center justify-center gap-4 mt-6">
        <button
          type="button"
          disabled={ending}
          onClick={() => (isRecording ? stopSession() : startSession())}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition disabled:opacity-60 ${
            isRecording
              ? "bg-red-600 hover:bg-red-700 text-white"
              : "bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-500/20"
          }`}
        >
          {ending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" /> Finishing…
            </>
          ) : isRecording ? (
            <>
              <VideoOff className="w-4 h-4" /> End Session
            </>
          ) : (
            <>
              <Video className="w-4 h-4" /> Start Posture Check
            </>
          )}
        </button>
      </div>
    </div>
  );
}
