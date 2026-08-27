"use client";

import LiveHUD from "@/components/live-hud";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-950">
      <header className="mb-6 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight text-white mb-1">
          PostureSense <span className="text-emerald-500">AI</span>
        </h1>
        <p className="text-slate-400 text-sm">
          Real-time posture coach — alerts you when you slouch, then coaches you back
        </p>
      </header>

      <div className="w-full max-w-6xl">
        <LiveHUD />
      </div>
    </main>
  );
}