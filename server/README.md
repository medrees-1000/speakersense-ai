# Person 1 — AI & Prompt Lead

This folder is the Gemini Live layer for **PostureSense**: a silent posture
evaluator that watches webcam frames and emits structured JSON for the HUD and
scorecard. Spoken alerts are delivered by the browser (SpeechSynthesis) from
`spoken_cue` — model audio is not played back into the room.

Person 2 owns the Next.js UI. Person 3 owns FastAPI WebSockets (`main.py`,
`live_stream.py`) and deployment. Do not duplicate prompts or parsing in those
layers — import from here.

## What was built

| File | Role |
| :--- | :--- |
| [app/gemini/client.py](app/gemini/client.py) | `google-genai` client, AUDIO Live config, JPEG blob helpers, token knobs |
| [app/gemini/prompts.py](app/gemini/prompts.py) | System instruction + Pydantic `LiveTick` / `SessionSummary` / `Exercise` |
| [app/utils/json_parser.py](app/utils/json_parser.py) | Stream-safe parser (fences, partial chunks, concatenated objects) |
| [app/gemini/live_stream.py](app/gemini/live_stream.py) | Browser ↔ Gemini Live WebSocket proxy |

Public imports:

```python
from app.gemini import (
    get_client,
    get_model_name,
    build_live_config,
    video_blob,
    ack_tool_call,
    SESSION_END_TEXT,
    TARGET_FPS,
    MAX_FRAME_WIDTH,
    JPEG_QUALITY,
    LiveTick,
    SessionSummary,
)
from app.utils import JsonStreamParser, parse_tool_call
```

Live API **does not** support `response_schema`. JSON is enforced by the system
prompt plus `JsonStreamParser`. Invalid objects are dropped so the WebSocket
loop does not crash.

## Env

Copy [`.env.example`](.env.example) to `server/.env` (never commit `.env`).

```
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-3.1-flash-live-preview
```

## Model compatibility

Default Live model: `gemini-3.1-flash-live-preview`.

**Native audio constraint:** this model does **not** support
`response_modalities=[TEXT]` (WebSocket 1011). `build_live_config()` uses
**AUDIO**, plus:

- `emit_live` / `emit_summary` tools (structured HUD/scorecard args)
- output audio transcription as a JSON-text fallback for `JsonStreamParser`

Do not flip the session back to TEXT. Do not play model audio to the user
(feedback loop). Spoken corrections use browser TTS on `spoken_cue`. Person 3
must **ack tool calls** (`ack_tool_call`) or the turn stalls.

Video on Live is capped at **1 FPS**.

## Media contract

| Knob | Value |
| :--- | :--- |
| Frame rate | `TARGET_FPS = 1` |
| Frame size | `MAX_FRAME_WIDTH = 640` |
| JPEG quality | `JPEG_QUALITY = 55` |

MIME type for frames: `image/jpeg` via `video_blob(jpeg_bytes)`.

## JSON contract

### Live tick (`type: "live"`) — HUD

```json
{
  "type": "live",
  "posture": "slouching",
  "severity": 2,
  "body_region": "spine",
  "alert": true,
  "spoken_cue": "Sit up — shoulders back.",
  "tip": "Unround your upper back."
}
```

| Field | Values |
| :--- | :--- |
| `posture` | `"good"` \| `"slouching"` \| `"leaning"` \| `"forward_head"` |
| `severity` | integer 0–3 |
| `body_region` | `"spine"` \| `"shoulders"` \| `"neck"` \| `"hips"` \| `"overall"` |
| `alert` | boolean — speak `spoken_cue` when true |
| `spoken_cue` | string, max 10 words |
| `tip` | string, max 12 words |

### Summary (`type: "summary"`) — scorecard

```json
{
  "type": "summary",
  "overall_score": 72,
  "posture_score": 68,
  "alignment_score": 74,
  "time_good_pct": 61,
  "slouch_events": 7,
  "worst_habit": "forward_head",
  "strengths": ["Kept hips square to camera"],
  "improvements": ["Round upper back when focusing"],
  "exercises": [
    {"name": "Chin tucks", "reps": "10 x 5s holds", "why": "Counters forward head"}
  ]
}
```

### Stop signal

```python
await session.send_realtime_input(text=SESSION_END_TEXT)  # "session_end"
```

## Browser WebSocket protocol

Endpoint: `WS /ws/stream`

- Client → server: `{"type":"video_frame","data":"<base64 jpeg>"}`
- Client → server: `{"type":"session_end"}`
- Server → client: live / summary JSON objects (same schemas as above)

## Setup and tests

```bash
cd server
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s . -p 'test_*.py' -v
uvicorn app.main:app --reload --port 8000
```
