"use client";

import { useEffect, useRef } from "react";
import { Video, VideoOff } from "lucide-react";

interface WebcamFeedProps {
    isActive: boolean;
}

export default function WebcamFeed({ isActive }: WebcamFeedProps) {
    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
        let stream: MediaStream | null = null;

        async function setupCamera() {
            if (isActive && videoRef.current) {
                try {
                    stream = await navigator.mediaDevices.getUserMedia({
                        video: true,
                        audio: true,
                    });
                    if (videoRef.current) {
                        videoRef.current.srcObject = stream;
                    }
                } catch (err) {
                    console.error("Camera access error:", err);
                }
            }
        }

        if (isActive) {
            setupCamera();
        } else if (videoRef.current && videoRef.current.srcObject) {
            const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
            tracks.forEach((track) => track.stop());
            videoRef.current.srcObject = null;
        }

        return () => {
            if (stream) {
                stream.getTracks().forEach((track) => track.stop());
            }
        };
    }, [isActive]);

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
        </div>
    );
}
