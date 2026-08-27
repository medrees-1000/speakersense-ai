"""Gemini Live SDK client, TEXT session config, and token/quota knobs.

Person 2: send JPEG ~1 FPS, max width 640, JPEG quality ~JPEG_QUALITY.
Render live.* gauges; when live.alert is true, speak live.spoken_cue with
browser SpeechSynthesis (the model's own voice is never played back — we
run in TEXT modality, so there is no model audio to worry about).
On stop, expect type: summary with exercises.

Person 3:
    client = get_client()
    config = build_live_config()
    async with client.aio.live.connect(model=get_model_name(), config=config) as session:
        await session.send_realtime_input(video=video_blob(jpeg_bytes))
        # Prefer tool calls (emit_live / emit_summary); ack them or the turn stalls.
        # Also feed any raw text chunks into JsonStreamParser as a fallback,
        # in case the model answers with a JSON string instead of a tool call.
        # on user stop:
        await session.send_realtime_input(text=SESSION_END_TEXT)
    Forward events as JSON over the browser WebSocket.
    Do not re-encode hotter than TARGET_FPS / MAX_FRAME_WIDTH / JPEG_QUALITY.

TEXT modality is used deliberately instead of the native-audio AUDIO
modality: tool-call cadence is far more reliable, and we never need the
model's spoken voice. See DEFAULT_MODEL below for why.
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
    SYSTEM_PROMPT,
)

# Token / quota knobs. Live video max is already 1 FPS.
TARGET_FPS = 1
MAX_FRAME_WIDTH = 640
JPEG_QUALITY = 55
AUDIO_SAMPLE_RATE = 16_000

# gemini-3.1-flash-live-preview is native-audio-first and only supports the
# AUDIO response modality — it is tuned for spoken conversation, not a silent
# once-a-second JSON heartbeat, and tool-call cadence was unreliable in
# testing (posture/severity ticks would go long stretches without firing).
# We never play the model's own voice back to the user (browser TTS handles
# spoken_cue instead), so native audio buys us nothing here. Use a
# TEXT-capable Live model instead — tool calling is far more reliable in
# TEXT mode. Override with GEMINI_MODEL in server/.env if you need to A/B
# test against the native-audio model.
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
                        "Report current posture, severity, body region, and "
                        "spoken alert cue for the live HUD."
                    ),
                    parameters=LIVE_TOOL_PARAMETERS,
                ),
                types.FunctionDeclaration(
                    name=SUMMARY_TOOL_NAME,
                    description=(
                        "Report the final posture scorecard and corrective "
                        "exercises after session_end."
                    ),
                    parameters=SUMMARY_TOOL_PARAMETERS,
                ),
            ]
        )
    ]


def build_live_config() -> types.LiveConnectConfig:
    """Live config set up for native audio model compatibility."""
    return types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        system_instruction=types.Content(
            parts=[types.Part(text=SYSTEM_PROMPT)]
        ),
        tools=_coaching_tools(),
    )


def ack_tool_call(function_call: types.FunctionCall) -> types.FunctionResponse:
    """Dummy tool result so the Live turn can continue (Live tool calls are synchronous)."""
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
