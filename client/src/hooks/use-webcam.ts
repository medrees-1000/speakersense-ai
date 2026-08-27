"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  FilesetResolver,
  PoseLandmarker,
  type NormalizedLandmark,
} from "@mediapipe/tasks-vision";
import type { PostureMetrics } from "../types/coaching";

export interface UseWebcamOptions {
  active: boolean;
  onFrame?: (metrics: PostureMetrics) => void;
}

function distance(a: NormalizedLandmark, b: NormalizedLandmark) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

export function useWebcam({ active, onFrame }: UseWebcamOptions) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const landmarkerRef = useRef<PoseLandmarker | null>(null);
  const animationRef = useRef<number | null>(null);
  const lastSpokenFrame = useRef(0);

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const analyze = useCallback(() => {
    const video = videoRef.current;
    const landmarker = landmarkerRef.current;

    if (!video || !landmarker || video.readyState < 2) {
      animationRef.current = requestAnimationFrame(analyze);
      return;
    }

    const result = landmarker.detectForVideo(video, performance.now());
    const landmarks = result.landmarks[0];

    if (landmarks) {
      const nose = landmarks[0];
      const leftShoulder = landmarks[11];
      const rightShoulder = landmarks[12];

      const shoulderMidpoint = {
        x: (leftShoulder.x + rightShoulder.x) / 2,
        y: (leftShoulder.y + rightShoulder.y) / 2,
      };

      const shoulderWidth = distance(leftShoulder, rightShoulder);
      const headOffset = Math.abs(nose.x - shoulderMidpoint.x) / shoulderWidth;
      const shoulderTilt =
        Math.abs(
          (Math.atan2(
            leftShoulder.y - rightShoulder.y,
            leftShoulder.x - rightShoulder.x,
          ) *
            180) /
            Math.PI,
        );

      let posture: PostureMetrics["posture"] = "good";
      let severity = 0;
      let tip = "Looking good";

      if (headOffset > 0.42) {
        posture = "leaning";
        severity = 2;
        tip = "Center your head over your shoulders";
      } else if (shoulderTilt > 13) {
        posture = "slouching";
        severity = 2;
        tip = "Level your shoulders";
      } else if (nose.y > shoulderMidpoint.y - shoulderWidth * 0.45) {
        posture = "forward_head";
        severity = 3;
        tip = "Bring your head back";
      }

      const metrics: PostureMetrics = {
        posture,
        severity,
        tip,
        headOffset: Math.round(headOffset * 100),
        shoulderTilt: Math.round(shoulderTilt),
        confidence: Math.round((landmarks[0].visibility ?? 0.8) * 100),
      };

      onFrame?.(metrics);

      if (
        severity >= 3 &&
        Date.now() - lastSpokenFrame.current > 7000 &&
        "speechSynthesis" in window
      ) {
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(
          new SpeechSynthesisUtterance("Please correct your posture"),
        );
        lastSpokenFrame.current = Date.now();
      }
    }

    animationRef.current = requestAnimationFrame(analyze);
  }, [onFrame]);

  useEffect(() => {
    if (!active) {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      return;
    }

    let cancelled = false;

    async function start() {
      try {
        setLoading(true);
        setError(null);

        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 1280, height: 720, facingMode: "user" },
          audio: false,
        });

        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        streamRef.current = stream;

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }

        const vision = await FilesetResolver.forVisionTasks(
          "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm",
        );

        landmarkerRef.current = await PoseLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath:
              "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
            delegate: "CPU",
          },
          runningMode: "VIDEO",
          numPoses: 1,
        });

        setLoading(false);
        animationRef.current = requestAnimationFrame(analyze);
      } catch (caught) {
        console.error("Posture startup failed:", caught);
        setLoading(false);

        const message =
          caught instanceof Error
            ? caught.message
            : caught instanceof Event
              ? "MediaPipe could not load. Check the browser console and network connection."
              : String(caught);

        setError(message);
      }
    }

    start();

    return () => {
      cancelled = true;
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      streamRef.current?.getTracks().forEach((track) => track.stop());
      landmarkerRef.current?.close();
      landmarkerRef.current = null;
    };
  }, [active, analyze]);

  return { videoRef, error, loading };
}
