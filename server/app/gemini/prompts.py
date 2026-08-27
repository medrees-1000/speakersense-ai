"""Posture coaching contract: system prompt + Pydantic schemas for Gemini Live.

Person 2: render `live` ticks on the HUD (posture, severity, tip) and speak
`spoken_cue` via browser TTS when `alert` is true. Sample JPEG at ~1 FPS,
max width 640. Render `summary` (scores + exercises) on the scorecard.

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

SYSTEM_PROMPT = """You are PostureSense, a silent posture coach.

You watch webcam frames of the user sitting or standing. You do NOT converse,
greet, ask questions, or chat in prose. Prefer function calls over speech.

Call emit_live about once per second with current posture metrics.
When the user text is exactly "session_end", call emit_summary once.

If you must vocalize, speak ONLY a single raw JSON object (same fields as the
tool). No markdown, no fences, no other words.

## What to evaluate (VIDEO frames only)

Judge the user's body alignment relative to the camera:

- posture:
  - "good" — upright spine, open chest, shoulders level, head stacked over torso
  - "slouching" — rounded upper back, collapsed chest, or slumped seat
  - "leaning" — torso tilted heavily left/right or twisted away from camera
  - "forward_head" — chin jutting forward / head ahead of shoulders (desk posture)

- severity: integer 0-3
  - 0 = good / negligible issue
  - 1 = mild
  - 2 = moderate
  - 3 = severe

- body_region: "spine" | "shoulders" | "neck" | "hips" | "overall"
  Pick the region that most needs correction right now.

- alert: true when posture is NOT "good" AND severity >= 2 (or any clear
  sustained bad posture worth interrupting the user about). false when good.

- spoken_cue: short spoken correction the UI will read aloud when alert is true.
  Max 10 words. Imperative and specific. Empty string when alert is false.
  Examples: "Sit up — shoulders back.", "Tuck your chin slightly.",
  "Unround your upper back."

- tip: optional on-screen coaching, max 12 words. Empty if nothing useful.

## Live updates (emit_live)

About once per second, call emit_live. Equivalent JSON if you must speak:

{"type":"live","posture":"slouching","severity":2,"body_region":"spine","alert":true,"spoken_cue":"Sit up — shoulders back.","tip":"Unround your upper back."}

Rules:
- posture must be one of: good, slouching, leaning, forward_head
- severity is an integer 0-3
- body_region must be one of: spine, shoulders, neck, hips, overall
- alert is a boolean
- spoken_cue max 10 words; empty when alert is false
- tip max 12 words; empty string if nothing useful
- No markdown, no code fences, no commentary before or after the JSON
- Do not wrap the object in an array

## Session end (emit_summary)

When the user text is exactly "session_end", call emit_summary once. Equivalent JSON:

{"type":"summary","overall_score":72,"posture_score":68,"alignment_score":74,"time_good_pct":61,"slouch_events":7,"worst_habit":"forward_head","strengths":["Kept hips square to camera"],"improvements":["Round upper back when focusing"],"exercises":[{"name":"Chin tucks","reps":"10 x 5s holds","why":"Counters forward head"},{"name":"Wall angels","reps":"2 sets of 8","why":"Opens tight shoulders"},{"name":"Seated thoracic extension","reps":"8 slow reps","why":"Unrounds the upper back"}]}

Rules:
- all scores and time_good_pct are integers 0-100
- slouch_events is an integer >= 0 (count of notable bad-posture episodes)
- worst_habit is one of: none, slouching, leaning, forward_head
- strengths and improvements are short string arrays (1-3 items)
- exercises: 2-4 objects with name, reps, why (each why max 12 words)
- No markdown, no prose around the JSON

If you are unsure about a visual metric, pick the closer enum rather than
explaining. Never apologize. Never say you cannot see the video — still emit JSON.
"""


class Posture(str, Enum):
    good = "good"
    slouching = "slouching"
    leaning = "leaning"
    forward_head = "forward_head"


class BodyRegion(str, Enum):
    spine = "spine"
    shoulders = "shoulders"
    neck = "neck"
    hips = "hips"
    overall = "overall"


class WorstHabit(str, Enum):
    none = "none"
    slouching = "slouching"
    leaning = "leaning"
    forward_head = "forward_head"


class LiveTick(BaseModel):
    """One HUD update. Person 2 binds gauges and TTS to these fields."""

    model_config = ConfigDict(extra="ignore")

    type: Literal["live"] = "live"
    posture: Posture
    severity: int = Field(ge=0, le=3)
    body_region: BodyRegion = BodyRegion.overall
    alert: bool = False
    spoken_cue: str = ""
    tip: str = ""

    @field_validator("severity", mode="before")
    @classmethod
    def _clamp_severity(cls, value: object) -> int:
        return min(3, max(0, int(round(float(value)))))  # type: ignore[arg-type]

    @field_validator("spoken_cue", mode="before")
    @classmethod
    def _truncate_spoken_cue(cls, value: object) -> str:
        if value is None:
            return ""
        words = str(value).strip().split()
        if len(words) > 10:
            return " ".join(words[:10])
        return " ".join(words)

    @field_validator("tip", mode="before")
    @classmethod
    def _truncate_tip(cls, value: object) -> str:
        if value is None:
            return ""
        words = str(value).strip().split()
        if len(words) > 12:
            return " ".join(words[:12])
        return " ".join(words)


class Exercise(BaseModel):
    """One corrective exercise on the end-of-session report."""

    model_config = ConfigDict(extra="ignore")

    name: str
    reps: str
    why: str = ""

    @field_validator("name", "reps", "why", mode="before")
    @classmethod
    def _stringify(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("why", mode="before")
    @classmethod
    def _truncate_why(cls, value: object) -> str:
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
    alignment_score: int = Field(ge=0, le=100)
    time_good_pct: int = Field(ge=0, le=100)
    slouch_events: int = Field(ge=0)
    worst_habit: WorstHabit = WorstHabit.none
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    exercises: list[Exercise] = Field(default_factory=list)

    @field_validator(
        "overall_score",
        "posture_score",
        "alignment_score",
        "time_good_pct",
        mode="before",
    )
    @classmethod
    def _clamp_score(cls, value: object) -> int:
        return min(100, max(0, int(round(float(value)))))  # type: ignore[arg-type]

    @field_validator("slouch_events", mode="before")
    @classmethod
    def _coerce_nonneg_int(cls, value: object) -> int:
        return max(0, int(round(float(value))))  # type: ignore[arg-type]


# OpenAPI-style tool parameters for Live API (no response_schema / parameters_json_schema).
LIVE_TOOL_PARAMETERS: dict = {
    "type": "object",
    "properties": {
        "posture": {
            "type": "string",
            "enum": ["good", "slouching", "leaning", "forward_head"],
        },
        "severity": {"type": "integer", "minimum": 0, "maximum": 3},
        "body_region": {
            "type": "string",
            "enum": ["spine", "shoulders", "neck", "hips", "overall"],
        },
        "alert": {"type": "boolean"},
        "spoken_cue": {"type": "string"},
        "tip": {"type": "string"},
    },
    "required": ["posture", "severity", "body_region", "alert"],
}

SUMMARY_TOOL_PARAMETERS: dict = {
    "type": "object",
    "properties": {
        "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "posture_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "alignment_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "time_good_pct": {"type": "integer", "minimum": 0, "maximum": 100},
        "slouch_events": {"type": "integer", "minimum": 0},
        "worst_habit": {
            "type": "string",
            "enum": ["none", "slouching", "leaning", "forward_head"],
        },
        "strengths": {"type": "array", "items": {"type": "string"}},
        "improvements": {"type": "array", "items": {"type": "string"}},
        "exercises": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "reps": {"type": "string"},
                    "why": {"type": "string"},
                },
                "required": ["name", "reps"],
            },
        },
    },
    "required": [
        "overall_score",
        "posture_score",
        "alignment_score",
        "time_good_pct",
        "slouch_events",
        "worst_habit",
    ],
}
