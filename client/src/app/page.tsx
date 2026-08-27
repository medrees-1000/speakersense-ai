"use client";

import { useCallback, useState } from "react";
import WebcamFeed from "../components/webcam-feed";
import LiveHud from "../components/live-hud";
import { useWebcam } from "../hooks/use-webcam";
import type { PostureMetrics } from "../types/coaching";
import Link from "next/link";

export default function HomePage() {
  const [active, setActive] = useState(false);
  const [metrics, setMetrics] = useState<PostureMetrics | null>(null);

  const handleFrame = useCallback((next: PostureMetrics) => {
    setMetrics(next);
  }, []);

  const { videoRef, error, loading } = useWebcam({
    active,
    onFrame: handleFrame,
  });

  return (
    <main className="min-h-screen bg-[#0b1225] px-6 py-8 text-white">
      <div className="mx-auto max-w-6xl space-y-6">
        <header>
          <h1 className="text-3xl font-bold">SpeakerSense AI</h1>
          <p className="mt-2 text-slate-400">
            Real-time posture coaching from your webcam
          </p>
        </header>

        <WebcamFeed
          active={active}
          videoRef={videoRef}
          metrics={metrics}
          loading={loading}
          error={error}
        />

        <LiveHud metrics={metrics} />

        <button
          type="button"
          onClick={() => setActive((value) => !value)}
          className="rounded-xl bg-emerald-500 px-6 py-3 font-semibold text-white"
        >
          {active ? "Stop Posture Check" : "Start Posture Check"}
        </button>

        <Link
          href="/summary"
          className="ml-4 inline-block rounded-xl border border-slate-700 px-6 py-3 text-white"
        >
          View Summary
        </Link>
      </div>
    </main>
  );
}