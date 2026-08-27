"use client";

import { useEffect, useRef } from "react";
import type { PostureMetrics } from "../types/coaching";

interface LiveHudProps {
  metrics: PostureMetrics | null;
}

function formatPosture(posture?: string): string {
  if (!posture) return "Waiting";
  return posture.replace("_", " ");
}

export default function LiveHud({ metrics }: LiveHudProps) {
  const lastCue = useRef("");

  useEffect(() => {
    if (!metrics || metrics.severity < 3 || metrics.tip === lastCue.current) {
      return;
    }

    lastCue.current = metrics.tip;

    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(
        new SpeechSynthesisUtterance(metrics.tip),
      );
    }
  }, [metrics]);

  const cards = [
    {
      label: "Posture",
      value: formatPosture(metrics?.posture),
      detail: metrics ? `${metrics.confidence}% confidence` : "Waiting",
      color: "text-emerald-400",
    },
    {
      label: "Severity",
      value: metrics ? `${metrics.severity}/3` : "—",
      detail: "0–3 scale",
      color: "text-amber-400",
    },
    {
      label: "Tip",
      value: metrics?.tip ?? "Looking good",
      detail: metrics ? `Head offset: ${metrics.headOffset}%` : "Idle",
      color: "text-cyan-400",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 text-center"
        >
          <div className={`text-sm font-semibold uppercase ${card.color}`}>
            {card.label}
          </div>
          <div className="mt-5 text-xl font-semibold capitalize text-white">
            {card.value}
          </div>
          <div className="mt-2 text-sm text-slate-500">{card.detail}</div>
        </div>
      ))}
    </div>
  );
}
