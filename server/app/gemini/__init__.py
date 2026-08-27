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
    audio_blob,
    build_live_config,
    get_client,
    get_model_name,
    video_blob,
)
from .prompts import (
    SESSION_END_TEXT,
    SYSTEM_INSTRUCTION,
    LiveTick,
    SessionSummary,
)

__all__ = [
    "AUDIO_SAMPLE_RATE",
    "DEFAULT_MODEL",
    "JPEG_QUALITY",
    "MAX_FRAME_WIDTH",
    "MODEL_NAME",
    "SESSION_END_TEXT",
    "SYSTEM_INSTRUCTION",
    "TARGET_FPS",
    "LiveTick",
    "SessionSummary",
    "audio_blob",
    "build_live_config",
    "get_client",
    "get_model_name",
    "video_blob",
]
