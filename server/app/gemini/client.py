"""Gemini Live SDK client, AUDIO session config, and token/quota knobs.

Person 2: send JPEG ~1 FPS, max width 640, JPEG quality ~JPEG_QUALITY.
Render live.* gauges; on stop, expect type: summary. Do not play model audio
back to the speaker (feedback loop).

Person 3:
    client = get_client()
    config = build_live_config()
    async with client.aio.live.connect(model=get_model_name(), config=config) as session:
        await session.send_realtime_input(audio=audio_blob(pcm_bytes))
        await session.send_realtime_input(video=video_blob(jpeg_bytes))
        # Prefer tool calls (emit_live / emit_summary); ack them or the turn stalls.
        # Also feed output transcription text into JsonStreamParser as a fallback.
        # on user stop:
        await session.send_realtime_input(text=SESSION_END_TEXT)
    Forward events as JSON over the browser WebSocket.
    Do not re-encode hotter than TARGET_FPS / MAX_FRAME_WIDTH / JPEG_QUALITY.

Current Live models are native-audio: TEXT response_modality returns 1011.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .prompts import (
    LIVE_TOOL_NAME,
    LIVE_TOOL_PARAMETERS,
    SESSION_END_TEXT,
    SUMMARY_TOOL_NAME,
    SUMMARY_TOOL_PARAMETERS,
    SYSTEM_INSTRUCTION,
)

# Token / quota knobs. Live video max is already 1 FPS.
TARGET_FPS = 1
MAX_FRAME_WIDTH = 640
JPEG_QUALITY = 55
AUDIO_SAMPLE_RATE = 16_000

# Gemini 3.1 Flash Live is the current Live API model (docs, Aug 2026).
# Retired / inactive: gemini-2.0-flash-live-001, gemini-live-2.5-flash-preview.
DEFAULT_MODEL = "gemini-3.1-flash-live-preview"
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


def _coaching_tools() -> list[types.Tool]:
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=LIVE_TOOL_NAME,
                    description=(
                        "Report current posture, eye contact, WPM, and filler "
                        "metrics for the live HUD."
                    ),
                    parameters=LIVE_TOOL_PARAMETERS,
                ),
                types.FunctionDeclaration(
                    name=SUMMARY_TOOL_NAME,
                    description="Report the final session scorecard after session_end.",
                    parameters=SUMMARY_TOOL_PARAMETERS,
                ),
            ]
        )
    ]


def build_live_config() -> types.LiveConnectConfig:
    """Native-audio Live config with coaching instruction and HUD tools.

    gemini-3.1-flash-live-preview only supports AUDIO response modality.
    output_audio_transcription lets JsonStreamParser still harvest JSON if the
    model speaks it. input_audio_transcription helps WPM / fillers.
    """
    return types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        system_instruction=types.Content(
            parts=[types.Part(text=SYSTEM_INSTRUCTION)]
        ),
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        tools=_coaching_tools(),
    )


def ack_tool_call(function_call: types.FunctionCall) -> types.FunctionResponse:
    """Dummy tool result so the Live turn can continue (3.1 tools are synchronous)."""
    return types.FunctionResponse(
        id=function_call.id,
        name=function_call.name or LIVE_TOOL_NAME,
        response={"ok": True},
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
