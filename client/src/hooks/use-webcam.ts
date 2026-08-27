"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const TARGET_FPS = 1;
const MAX_FRAME_WIDTH = 640;
const JPEG_QUALITY = 0.55;

export interface UseWebcamOptions {
  active: boolean;
  onFrame?: (base64Jpeg: string) => void;
}

export function useWebcam({ active, onFrame }: UseWebcamOptions) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const onFrameRef = useRef(onFrame);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    onFrameRef.current = onFrame;
  }, [onFrame]);

  const attachVideo = useCallback((node: HTMLVideoElement | null) => {
    videoRef.current = node;
    if (node && streamRef.current) {
      node.srcObject = streamRef.current;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    async function start() {
      setError(null);
      setReady(false);
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user" },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        setReady(true);

        if (!canvasRef.current) {
          canvasRef.current = document.createElement("canvas");
        }

        const sampleMs = Math.round(1000 / TARGET_FPS);
        intervalId = setInterval(() => {
          const video = videoRef.current;
          const canvas = canvasRef.current;
          const callback = onFrameRef.current;
          if (!video || !canvas || !callback || video.readyState < 2) return;

          const srcW = video.videoWidth || 640;
          const srcH = video.videoHeight || 480;
          const scale = Math.min(1, MAX_FRAME_WIDTH / srcW);
          const width = Math.round(srcW * scale);
          const height = Math.round(srcH * scale);
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext("2d");
          if (!ctx) return;
          ctx.drawImage(video, 0, 0, width, height);
          const dataUrl = canvas.toDataURL("image/jpeg", JPEG_QUALITY);
          const base64 = dataUrl.split(",")[1];
          if (base64) callback(base64);
        }, sampleMs);
      } catch (err) {
        console.error("Camera access error:", err);
        if (!cancelled) {
          setError("Camera access denied or unavailable.");
        }
      }
    }

    function stop() {
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      setReady(false);
    }

    if (active) {
      start();
    } else {
      stop();
    }

    return () => {
      cancelled = true;
      stop();
    };
  }, [active]);

  return { attachVideo, ready, error };
}
