"use client";

import type { RefObject } from "react";
import type { PostureMetrics } from "../types/coaching";

interface WebcamFeedProps {
  active: boolean;
  videoRef: RefObject<HTMLVideoElement>;
  metrics: PostureMetrics | null;
  loading?: boolean;
  error?: string | null;
}

export default function WebcamFeed({
  active,
  videoRef,
  metrics,
  loading,
  error,
}: WebcamFeedProps) {
  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-2xl bg-slate-950">
      <video
        ref={videoRef}
        muted
        playsInline
        className={`h-full w-full object-cover ${active ? "" : "hidden"}`}
      />

      {!active && (
        <div className="flex h-full items-center justify-center text-slate-400">
          Camera paused
        </div>
      )}

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/40 text-white">
          Starting posture detection…
        </div>
      )}

      {error && (
        <div className="absolute bottom-3 left-3 right-3 rounded-lg bg-red-500/90 p-3 text-sm text-white">
          {error}
        </div>
      )}

      {metrics && active && (
        <div className="absolute left-4 top-4 rounded-xl bg-slate-950/80 px-4 py-3 text-white">
          <div className="text-xs uppercase tracking-wider text-emerald-300">
            Live posture
          </div>
          <div className="font-semibold">{metrics.posture.replace("_", " ")}</div>
        </div>
      )}
    </div>
  );
}