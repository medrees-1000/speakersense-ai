"use client";

import { Video, VideoOff } from "lucide-react";

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
    <div className="relative aspect-video w-full bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex items-center justify-center">
      {isActive ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover transform -scale-x-100"
        />
      ) : (
        <div className="flex flex-col items-center justify-center text-slate-500 gap-2">
          <VideoOff className="w-10 h-10 stroke-[1.5]" />
          <span className="text-sm">Camera inactive</span>
        </div>
      )}

      {isActive && (
        <div className="absolute top-3 right-3 flex items-center gap-2 bg-red-500/20 border border-red-500/40 px-2.5 py-1 rounded-full text-xs font-semibold text-red-400">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
          LIVE
        </div>
      )}

      {isActive && postureLabel && (
        <div
          className={`absolute bottom-3 left-3 px-3 py-1.5 rounded-lg text-xs font-semibold border ${
            alerting
              ? "bg-amber-500/20 border-amber-500/50 text-amber-200"
              : "bg-emerald-500/15 border-emerald-500/40 text-emerald-200"
          }`}
        >
          {postureLabel}
        </div>
      )}
    </div>
  );
}
