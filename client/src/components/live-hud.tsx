"use client";

import { useState } from "react";
import Link from "next/link";
import WebcamFeed from "./webcam-feed";
import { Mic, MicOff, Gauge, MessageSquareWarning, Sparkles, ArrowRight } from "lucide-react";

export default function LiveHUD() {
    const [isRecording, setIsRecording] = useState(false);

    return (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 backdrop-blur shadow-2xl">
            <WebcamFeed isActive={isRecording} />

            {/* Real-time Metric Cards */}
            <div className="grid grid-cols-3 gap-4 mt-6">
                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl text-center">
                    <div className="flex items-center justify-center text-blue-400 gap-1.5 mb-1">
                        <Gauge className="w-4 h-4" />
                        <span className="text-xs font-semibold uppercase">Pace</span>
                    </div>
                    <div className="text-2xl font-bold text-white">135</div>
                    <div className="text-xs text-slate-500">WPM (Ideal)</div>
                </div>

                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl text-center">
                    <div className="flex items-center justify-center text-amber-400 gap-1.5 mb-1">
                        <MessageSquareWarning className="w-4 h-4" />
                        <span className="text-xs font-semibold uppercase">Fillers</span>
                    </div>
                    <div className="text-2xl font-bold text-white">2</div>
                    <div className="text-xs text-slate-500">"um", "like"</div>
                </div>

                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl text-center">
                    <div className="flex items-center justify-center text-emerald-400 gap-1.5 mb-1">
                        <Sparkles className="w-4 h-4" />
                        <span className="text-xs font-semibold uppercase">Clarity</span>
                    </div>
                    <div className="text-2xl font-bold text-white">94%</div>
                    <div className="text-xs text-slate-500">High engagement</div>
                </div>
            </div>

            {/* Control Buttons */}
            <div className="flex items-center justify-center gap-4 mt-6">
                <button
                    onClick={() => setIsRecording(!isRecording)}
                    className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition ${isRecording
                        ? "bg-red-600 hover:bg-red-700 text-white"
                        : "bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/20"
                        }`}
                >
                    {isRecording ? (
                        <>
                            <MicOff className="w-4 h-4" /> Stop Session
                        </>
                    ) : (
                        <>
                            <Mic className="w-4 h-4" /> Start Practice
                        </>
                    )}
                </button>

                <Link
                    href="/summary"
                    className="flex items-center gap-1.5 px-4 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium transition"
                >
                    View Summary <ArrowRight className="w-4 h-4" />
                </Link>
            </div>
        </div>
    );
}
