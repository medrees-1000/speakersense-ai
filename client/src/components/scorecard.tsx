"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Dumbbell,
  Gauge,
} from "lucide-react";
import {
  SUMMARY_STORAGE_KEY,
  type SessionSummary,
} from "@/types/coaching";

const FALLBACK: SessionSummary = {
  type: "summary",
  overall_score: 72,
  posture_score: 68,
  alignment_score: 74,
  time_good_pct: 61,
  slouch_events: 7,
  worst_habit: "forward_head",
  strengths: ["Kept hips square to the camera"],
  improvements: ["Watch forward-head posture at the desk"],
  exercises: [
    {
      name: "Chin tucks",
      reps: "10 × 5s holds",
      why: "Counters forward head",
    },
    {
      name: "Wall angels",
      reps: "2 sets of 8",
      why: "Opens tight shoulders",
    },
    {
      name: "Seated thoracic extension",
      reps: "8 slow reps",
      why: "Unrounds the upper back",
    },
  ],
};

function formatHabit(habit: string): string {
  if (habit === "none") return "None detected";
  return habit.replace(/_/g, " ");
}

export default function Scorecard() {
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [fromSession, setFromSession] = useState(false);

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(SUMMARY_STORAGE_KEY);
      if (raw) {
        setSummary(JSON.parse(raw) as SessionSummary);
        setFromSession(true);
        return;
      }
    } catch {
      // fall through
    }
    setSummary(FALLBACK);
    setFromSession(false);
  }, []);

  if (!summary) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 max-w-2xl w-full text-slate-400 text-sm">
        Loading report…
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 max-w-2xl w-full">
      <h2 className="text-2xl font-bold text-white mb-1">Posture Report</h2>
      <p className="text-slate-400 text-sm mb-6">
        {fromSession
          ? "AI analysis of your posture session"
          : "Sample report — run a live session to see your results"}
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
        {[
          { label: "Overall", value: summary.overall_score },
          { label: "Posture", value: summary.posture_score },
          { label: "Alignment", value: summary.alignment_score },
          { label: "Time good", value: `${summary.time_good_pct}%` },
        ].map((item) => (
          <div
            key={item.label}
            className="bg-slate-950/70 border border-slate-800 rounded-xl p-3 text-center"
          >
            <div className="flex items-center justify-center gap-1 text-sky-400 mb-1">
              <Gauge className="w-3.5 h-3.5" />
              <span className="text-[10px] font-semibold uppercase tracking-wide">
                {item.label}
              </span>
            </div>
            <div className="text-xl font-bold text-white">{item.value}</div>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-3 text-xs text-slate-300 mb-8">
        <span className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800">
          Slouch events: <strong className="text-white">{summary.slouch_events}</strong>
        </span>
        <span className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 capitalize">
          Worst habit:{" "}
          <strong className="text-white">{formatHabit(summary.worst_habit)}</strong>
        </span>
      </div>

      <div className="space-y-3 mb-8">
        {summary.strengths.map((item) => (
          <div
            key={item}
            className="flex items-start gap-3 p-4 bg-emerald-950/20 border border-emerald-800/40 rounded-xl"
          >
            <CheckCircle2 className="w-5 h-5 text-emerald-400 mt-0.5 shrink-0" />
            <div>
              <h4 className="font-semibold text-emerald-300 text-sm">Strength</h4>
              <p className="text-xs text-slate-300">{item}</p>
            </div>
          </div>
        ))}
        {summary.improvements.map((item) => (
          <div
            key={item}
            className="flex items-start gap-3 p-4 bg-amber-950/20 border border-amber-800/40 rounded-xl"
          >
            <AlertCircle className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
            <div>
              <h4 className="font-semibold text-amber-300 text-sm">Improve</h4>
              <p className="text-xs text-slate-300">{item}</p>
            </div>
          </div>
        ))}
      </div>

      {summary.exercises.length > 0 && (
        <div className="mb-8">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Dumbbell className="w-4 h-4 text-sky-400" />
            Recommended exercises
          </h3>
          <div className="space-y-3">
            {summary.exercises.map((ex) => (
              <div
                key={`${ex.name}-${ex.reps}`}
                className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl"
              >
                <div className="flex items-baseline justify-between gap-3">
                  <h4 className="font-semibold text-slate-100 text-sm">{ex.name}</h4>
                  <span className="text-xs text-sky-300 shrink-0">{ex.reps}</span>
                </div>
                {ex.why && (
                  <p className="text-xs text-slate-400 mt-1">{ex.why}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <Link
        href="/"
        className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-medium transition"
      >
        <ArrowLeft className="w-4 h-4" /> Start New Session
      </Link>
    </div>
  );
}
