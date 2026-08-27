import Link from "next/link";
import { ArrowLeft, CheckCircle2, AlertCircle } from "lucide-react";

export default function Scorecard() {
    return (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 max-w-2xl w-full">
            <h2 className="text-2xl font-bold text-white mb-1">Session Scorecard</h2>
            <p className="text-slate-400 text-sm mb-6">AI analysis of your speech delivery</p>

            <div className="space-y-4 mb-8">
                <div className="flex items-start gap-3 p-4 bg-emerald-950/20 border border-emerald-800/40 rounded-xl">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400 mt-0.5" />
                    <div>
                        <h4 className="font-semibold text-emerald-300 text-sm">Great Energy & Pacing</h4>
                        <p className="text-xs text-slate-300">Maintained an average of 135 WPM throughout.</p>
                    </div>
                </div>

                <div className="flex items-start gap-3 p-4 bg-amber-950/20 border border-amber-800/40 rounded-xl">
                    <AlertCircle className="w-5 h-5 text-amber-400 mt-0.5" />
                    <div>
                        <h4 className="font-semibold text-amber-300 text-sm">Filler Word Spike</h4>
                        <p className="text-xs text-slate-300">Detected 4 uses of "um" during transition sections.</p>
                    </div>
                </div>
            </div>

            <Link
                href="/"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-medium transition"
            >
                <ArrowLeft className="w-4 h-4" /> Start New Session
            </Link>
        </div>
    );
}
