"""Stream-safe JSON extractor for Gemini Live output.

Person 3: feed output-transcription fragments into JsonStreamParser.feed.
Also call parse_tool_call() for emit_live / emit_summary function calls,
then ack with ack_tool_call() or the native-audio turn stalls.
"""

from __future__ import annotations

import json
import re
from typing import Any, Union

from pydantic import ValidationError

from ..gemini.prompts import (
    LIVE_TOOL_NAME,
    LiveTick,
    SessionSummary,
    SUMMARY_TOOL_NAME,
)

CoachingEvent = Union[LiveTick, SessionSummary]

# ```json, ```JSON, or bare ``` — including leftover closing fences.
_FENCE_RE = re.compile(r"```(?:json)?\s*", re.IGNORECASE)


def _strip_fences(text: str) -> str:
    return _FENCE_RE.sub("", text)


def _extract_object(buffer: str) -> tuple[str | None, int]:
    """Return (object_text, end_index) for the next complete `{...}`, or (None, keep_from).

    keep_from is the index to retain in the buffer when the object is incomplete
    (leading chatter before `{` is dropped).
    """
    start = buffer.find("{")
    if start == -1:
        return None, 0 if not buffer.strip() else 0

    depth = 0
    in_string = False
    escape = False
    for index, char in enumerate(buffer[start:], start):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return buffer[start : index + 1], index + 1
    return None, start


def _parse_event(raw: str) -> CoachingEvent | None:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None

    kind = str(payload.get("type", "")).strip().lower()
    try:
        if kind == "live":
            payload["type"] = "live"
            return LiveTick.model_validate(payload)
        if kind == "summary":
            payload["type"] = "summary"
            return SessionSummary.model_validate(payload)
    except (ValidationError, ValueError, TypeError):
        return None
    return None


def parse_tool_call(name: str | None, args: dict[str, Any] | None) -> CoachingEvent | None:
    """Validate emit_live / emit_summary tool arguments into a coaching event."""
    if not name or not isinstance(args, dict):
        return None
    if name == LIVE_TOOL_NAME:
        payload: dict[str, Any] = {"type": "live", **args}
        return _parse_event(json.dumps(payload))
    if name == SUMMARY_TOOL_NAME:
        payload = {"type": "summary", **args}
        return _parse_event(json.dumps(payload))
    return None


class JsonStreamParser:
    """Accumulate Gemini text chunks and emit complete coaching events."""

    def __init__(self) -> None:
        self._buffer = ""

    def reset(self) -> None:
        self._buffer = ""

    def feed(self, chunk: str | None) -> list[CoachingEvent]:
        if not chunk:
            return []
        self._buffer = _strip_fences(self._buffer + chunk)

        events: list[CoachingEvent] = []
        while True:
            raw, consumed = _extract_object(self._buffer)
            if raw is None:
                # Incomplete object: keep from `{`. If no `{`, drop chatter.
                self._buffer = self._buffer[consumed:]
                if "{" not in self._buffer:
                    self._buffer = ""
                break
            event = _parse_event(raw)
            if event is not None:
                events.append(event)
            self._buffer = self._buffer[consumed:]
        return events
