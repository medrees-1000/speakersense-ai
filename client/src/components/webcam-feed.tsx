"use client";

import { RefObject } from "react";

interface WebcamFeedProps {
  videoRef: (node: HTMLVideoElement | null) => void;
  isActive: boolean;
  postureLabel?: string;
  alerting?: boolean;
}

export default function WebcamFeed({
  videoRef,
  isActive,
  postureLabel,
  alerting = false,
}: WebcamFeedProps) {
  return (
    <div className="relative w-full max-w-3xl mx-auto aspect-video bg-slate-950 rounded-xl overflow-hidden border border-slate-800 shadow-inner">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className={`w-full h-full object-cover transform -scale-x-100 transition-opacity duration-300 ${
          isActive ? "opacity-100" : "opacity-20"
        }`}
      />

      {!isActive && (
        <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm font-medium">
          Camera feed inactive
        </div>
      )}

      {isActive && postureLabel && (
        <div
          className={`absolute top-4 left-4 px-3 py-1.5 rounded-lg text-xs font-semibold backdrop-blur transition-colors ${
            alerting
              ? "bg-red-500/80 text-white animate-pulse"
              : "bg-slate-900/80 text-emerald-400 border border-slate-700"
          }`}
        >
          {postureLabel}
        </div>
      )}
    </div>
  );
}