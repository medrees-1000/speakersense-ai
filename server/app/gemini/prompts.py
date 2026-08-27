"""Coaching contract: system prompt + Pydantic schemas for Gemini Live JSON.

Person 2: render `live` ticks on HUD gauges (posture, eye_contact, wpm,
filler_count) and `summary` on the scorecard after stop. Sample JPEG at
~1 FPS, max width 640.

Person 3: on session stop, send realtime text SESSION_END_TEXT so Gemini
emits one summary object. Forward parser output as JSON over the browser WS.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Person 3 sends this as realtime text when the user hits stop.
SESSION_END_TEXT = "session_end"

LIVE_TOOL_NAME = "emit_live"
SUMMARY_TOOL_NAME = "emit_summary"

SYSTEM_PROMPT = """You are SpeakerSense, a silent public-speaking evaluator.

You watch webcam frames and listen to microphone audio. You do NOT converse,
greet, ask questions, or coach in prose. Prefer function calls over speech.

Call emit_live about once per second with current metrics.
When the user text is exactly "session_end", call emit_summary once.

If you must vocalize, speak ONLY a single raw JSON object (same fields as the
tool). No markdown, no fences, no other words.

## What to evaluate

From VIDEO frames:
- posture: "good" if the speaker is upright with open shoulders; "slouching"
  if they hunch, collapse the chest, or lean heavily.
- eye_contact: "engaged" if they look toward the camera; "looking_away" if
  they look down, away, or off-screen.

From AUDIO:
- wpm: estimated words per minute of recent speech (integer). If silent, 0.
- filler_count: cumulative count of fillers so far this session
  (um, uh, like, you know, so, actually, kinda, sort of).

## Live updates (emit_live)

About once per second, call emit_live. Equivalent JSON if you must speak:

{"type":"live","posture":"good","eye_contact":"engaged","wpm":142,"filler_count":4,"tip":"Lift your chin toward the camera."}

Rules:
- posture must be "good" or "slouching"
- eye_contact must be "engaged" or "looking_away"
- wpm and filler_count are integers >= 0
- tip is optional coaching, max 12 words. Empty string if nothing useful.
- No markdown, no code fences, no commentary before or after the JSON.
- Do not wrap the object in an array.

## Session end (emit_summary)

When the user text is exactly "session_end", call emit_summary once. Equivalent JSON:

{"type":"summary","overall_score":78,"posture_score":80,"eye_contact_score":72,"pace_score":85,"filler_score":64,"avg_wpm":145,"total_fillers":12,"strengths":["Steady pace"],"improvements":["Watch filler like"]}

Rules:
- all scores are integers 0-100
- avg_wpm and total_fillers are integers >= 0
- strengths and improvements are short string arrays (1-3 items)
- No markdown, no extra keys required, no prose around the JSON.

If you are unsure about a visual metric, pick the closer enum rather than
explaining. Never apologize. Never say you cannot see the video — still emit JSON.
"""


class Posture(str, Enum):
    good = "good"
    slouching = "slouching"


class EyeContact(str, Enum):
    engaged = "engaged"
    looking_away = "looking_away"


class LiveTick(BaseModel):
    """One HUD update. Person 2 binds gauges to these fields."""

    model_config = ConfigDict(extra="ignore")

    type: Literal["live"] = "live"
    posture: Posture
    eye_contact: EyeContact
    wpm: int = Field(ge=0)
    filler_count: int = Field(ge=0)
    tip: str = ""

    @field_validator("wpm", "filler_count", mode="before")
    @classmethod
    def _coerce_nonneg_int(cls, value: object) -> int:
        return max(0, int(round(float(value))))  # type: ignore[arg-type]

    @field_validator("tip", mode="before")
    @classmethod
    def _truncate_tip(cls, value: object) -> str:
        if value is None:
            return ""
        words = str(value).strip().split()
        if len(words) > 12:
            return " ".join(words[:12])
        return " ".join(words)


class SessionSummary(BaseModel):
    """Final scorecard payload after session_end."""

    model_config = ConfigDict(extra="ignore")

    type: Literal["summary"] = "summary"
    overall_score: int = Field(ge=0, le=100)
    posture_score: int = Field(ge=0, le=100)
    eye_contact_score: int = Field(ge=0, le=100)
    pace_score: int = Field(ge=0, le=100)
    filler_score: int = Field(ge=0, le=100)
    avg_wpm: int = Field(ge=0)
    total_fillers: int = Field(ge=0)
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)

    @field_validator(
        "overall_score",
        "posture_score",
        "eye_contact_score",
        "pace_score",
        "filler_score",
        mode="before",
    )
    @classmethod
    def _clamp_score(cls, value: object) -> int:
        return min(100, max(0, int(round(float(value)))))  # type: ignore[arg-type]

    @field_validator("avg_wpm", "total_fillers", mode="before")
    @classmethod
    def _coerce_nonneg_int(cls, value: object) -> int:
        return max(0, int(round(float(value))))  # type: ignore[arg-type]


# OpenAPI-style tool parameters for Live API (no response_schema / parameters_json_schema).
LIVE_TOOL_PARAMETERS: dict = {
    "type": "object",
    "properties": {
        "posture": {"type": "string", "enum": ["good", "slouching"]},
        "eye_contact": {"type": "string", "enum": ["engaged", "looking_away"]},
        "wpm": {"type": "integer", "minimum": 0},
        "filler_count": {"type": "integer", "minimum": 0},
        "tip": {"type": "string"},
    },
    "required": ["posture", "eye_contact", "wpm", "filler_count"],
}

SUMMARY_TOOL_PARAMETERS: dict = {
    "type": "object",
    "properties": {
        "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "posture_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "eye_contact_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "pace_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "filler_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "avg_wpm": {"type": "integer", "minimum": 0},
        "total_fillers": {"type": "integer", "minimum": 0},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "improvements": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "overall_score",
        "posture_score",
        "eye_contact_score",
        "pace_score",
        "filler_score",
        "avg_wpm",
        "total_fillers",
    ],
}
