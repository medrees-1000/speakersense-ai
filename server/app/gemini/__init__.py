"""Gemini Live client, prompts, and JSON contract for SpeakerSense.

Person 3 should import from here rather than reaching into submodules.
"""

from .client import (
    AUDIO_SAMPLE_RATE,
    DEFAULT_MODEL,
    JPEG_QUALITY,
    MAX_FRAME_WIDTH,
    MODEL_NAME,
    TARGET_FPS,
    ack_tool_call,
    audio_blob,
    build_live_config,
    get_client,
    get_model_name,
    video_blob,
)
from .prompts import (
    LIVE_TOOL_NAME,
    SESSION_END_TEXT,
    SUMMARY_TOOL_NAME,
    SYSTEM_PROMPT,
    LiveTick,
    SessionSummary,
)

__all__ = [
    "AUDIO_SAMPLE_RATE",
    "DEFAULT_MODEL",
    "JPEG_QUALITY",
    "LIVE_TOOL_NAME",
    "MAX_FRAME_WIDTH",
    "MODEL_NAME",
    "SESSION_END_TEXT",
    "SUMMARY_TOOL_NAME",
    "SYSTEM_PROMPT",
    "TARGET_FPS",
    "LiveTick",
    "SessionSummary",
    "ack_tool_call",
    "audio_blob",
    "build_live_config",
    "get_client",
    "get_model_name",
    "video_blob",
]
