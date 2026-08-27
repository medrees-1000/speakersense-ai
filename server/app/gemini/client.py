"""Gemini Live SDK client, TEXT session config, and token/quota knobs.

Person 2: send JPEG ~1 FPS, max width 640, JPEG quality ~JPEG_QUALITY.
Render live.* gauges; on stop, expect type: summary.

Person 3:
    client = get_client()
    config = build_live_config()
    async with client.aio.live.connect(model=get_model_name(), config=config) as session:
        await session.send_realtime_input(audio=audio_blob(pcm_bytes))
        await session.send_realtime_input(video=video_blob(jpeg_bytes))
        # on user stop:
        await session.send_realtime_input(text=SESSION_END_TEXT)
    Forward JsonStreamParser output as JSON over the browser WebSocket.
    Do not re-encode hotter than TARGET_FPS / MAX_FRAME_WIDTH / JPEG_QUALITY.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .prompts import SESSION_END_TEXT, SYSTEM_INSTRUCTION

# Token / quota knobs. Live video max is already 1 FPS.
TARGET_FPS = 1
MAX_FRAME_WIDTH = 640
JPEG_QUALITY = 55
AUDIO_SAMPLE_RATE = 16_000

# Retired: gemini-2.0-flash-live-001. Use a TEXT-capable Live model, not native-audio-only.
DEFAULT_MODEL = "gemini-live-2.5-flash-preview"
MODEL_NAME = DEFAULT_MODEL

_SERVER_DIR = Path(__file__).resolve().parents[2]


def _load_env() -> None:
    load_dotenv(_SERVER_DIR / ".env")
    load_dotenv()


def get_model_name() -> str:
    """Live model id. Override with GEMINI_MODEL in server/.env."""
    _load_env()
    name = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL).strip()
    return name or DEFAULT_MODEL


def get_client() -> genai.Client:
    """Build a google-genai client. Raises if GEMINI_API_KEY is missing."""
    _load_env()
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy server/.env.example to server/.env "
            "and add your Gemini API key."
        )
    return genai.Client(api_key=api_key)


def build_live_config() -> types.LiveConnectConfig:
    """TEXT-modality Live config with coaching system instruction.

    input_audio_transcription gives the model a speech trace for WPM / fillers
    even though we request TEXT output (not a talking coach).
    """
    return types.LiveConnectConfig(
        response_modalities=[types.Modality.TEXT],
        system_instruction=types.Content(
            parts=[types.Part(text=SYSTEM_INSTRUCTION)]
        ),
        input_audio_transcription=types.AudioTranscriptionConfig(),
    )


def audio_blob(pcm_bytes: bytes) -> types.Blob:
    """16-bit little-endian PCM at AUDIO_SAMPLE_RATE for send_realtime_input(audio=...)."""
    return types.Blob(
        data=pcm_bytes,
        mime_type=f"audio/pcm;rate={AUDIO_SAMPLE_RATE}",
    )


def video_blob(jpeg_bytes: bytes) -> types.Blob:
    """JPEG frame for send_realtime_input(video=...). Person 2 samples at TARGET_FPS."""
    return types.Blob(data=jpeg_bytes, mime_type="image/jpeg")


def main() -> None:
    print(f"TARGET_FPS={TARGET_FPS}")
    print(f"MAX_FRAME_WIDTH={MAX_FRAME_WIDTH}")
    print(f"JPEG_QUALITY={JPEG_QUALITY}")
    print(f"AUDIO_SAMPLE_RATE={AUDIO_SAMPLE_RATE}")
    print(f"SESSION_END_TEXT={SESSION_END_TEXT}")
    print(f"model={get_model_name()}")
    get_client()
    build_live_config()
    print("client ok")


if __name__ == "__main__":
    main()
