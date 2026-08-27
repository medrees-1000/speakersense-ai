# Person 1 — AI & Prompt Lead

This folder is the Gemini Live layer for SpeakerSense: a **silent speaking evaluator**, not a chatbot. The model watches webcam frames and listens to the mic, then emits **raw JSON** for the HUD and scorecard.

Person 2 owns the Next.js UI. Person 3 owns FastAPI WebSockets (`main.py`, `live_stream.py`) and deployment. Do not duplicate prompts or parsing in those layers — import from here.

## What was built

| File | Role |
| :--- | :--- |
| [app/gemini/client.py](app/gemini/client.py) | `google-genai` client, AUDIO Live config, PCM/JPEG blob helpers, token knobs |
| [app/gemini/prompts.py](app/gemini/prompts.py) | System instruction + Pydantic `LiveTick` / `SessionSummary` |
| [app/utils/json_parser.py](app/utils/json_parser.py) | Stream-safe parser (fences, partial chunks, concatenated objects) |

Public imports (Person 3 should use these, not deep submodule paths):

```python
from app.gemini import (
    get_client,
    get_model_name,
    build_live_config,
    audio_blob,
    video_blob,
    ack_tool_call,
    SESSION_END_TEXT,
    TARGET_FPS,
    MAX_FRAME_WIDTH,
    JPEG_QUALITY,
    AUDIO_SAMPLE_RATE,
    LiveTick,
    SessionSummary,
)
from app.utils import JsonStreamParser, parse_tool_call
```

Live API **does not** support `response_schema`. JSON is enforced by the system prompt plus `JsonStreamParser`. Invalid objects are dropped so the WebSocket loop does not crash.

## Env

Copy [`.env.example`](.env.example) to `server/.env` (never commit `.env`).

```
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-3.1-flash-live-preview
```

`get_client()` loads `server/.env`, then a `.env` in the process working directory. It raises `RuntimeError` if `GEMINI_API_KEY` is missing.

`get_model_name()` reads `GEMINI_MODEL` at call time. Prefer that over the module constant `MODEL_NAME` (import-time default only).

## Model compatibility (important)

As of the [Gemini models list](https://ai.google.dev/gemini-api/docs/models) (27 Aug 2026), the Live API models are:

| Model | Endpoint | Use here? |
| :--- | :--- | :--- |
| **Gemini 3.1 Flash Live** | `gemini-3.1-flash-live-preview` | **Yes — default.** Inputs: text, images, audio, video. Current Live API model. |
| Gemini 2.5 Flash Live | `gemini-2.5-flash-native-audio-preview-12-2025` | Older native-audio Live; Google tells you to migrate to 3.1. |
| Gemini 3.5 Live Translate | `gemini-3.5-live-translate-preview` | No — speech-to-speech translation only. |
| `gemini-live-2.5-flash-preview` / `gemini-2.0-flash-live-001` | — | Inactive / retired. Do not use. |

`gemini-3.7-flash` is the latest general Flash model, but it is **not** a Live API model. SpeakerSense streams mic + webcam over Live WebSockets, so we stay on Flash Live.

**Native audio constraint:** `gemini-3.1-flash-live-preview` does **not** support `response_modalities=[TEXT]` (WebSocket 1011). `build_live_config()` uses **AUDIO**, plus:

- `emit_live` / `emit_summary` tools (structured HUD/scorecard args — Live has no `response_schema`)
- output audio transcription as a JSON-text fallback for `JsonStreamParser`
- input audio transcription for WPM / fillers

Do not flip the session back to TEXT. Do not play model audio to the presenter (feedback loop). Person 3 must **ack tool calls** (`ack_tool_call`) or the turn stalls — 3.1 Live function calling is synchronous.

Video on Live is capped at **1 FPS**. Sending faster wastes quota and does not improve posture/eye-contact.

## Media contract (Person 2 + Person 3)

Match these knobs or Gemini will get worse signal per token:

| Knob | Value | Who |
| :--- | :--- | :--- |
| Frame rate | `TARGET_FPS = 1` | Person 2 canvas sample rate |
| Frame size | `MAX_FRAME_WIDTH = 640` | Person 2 downscale before JPEG |
| JPEG quality | `JPEG_QUALITY = 55` | Person 2 `toBlob` / canvas quality |
| Audio | 16-bit little-endian PCM, `AUDIO_SAMPLE_RATE = 16000` | Person 2 capture; Person 3 wrap with `audio_blob()` |

Person 3 must **not** re-encode hotter than this. MIME types:

- Audio: `audio/pcm;rate=16000` via `audio_blob(pcm_bytes)`
- Video: `image/jpeg` via `video_blob(jpeg_bytes)`

## JSON contract (Person 2 HUD + scorecard)

Forward parser events with `event.model_dump()` (or `model_dump(mode="json")` so enums become strings). Discriminate on `type`.

### Live tick (`type: "live"`) — HUD

Emitted about once per second while the session is open.

```json
{
  "type": "live",
  "posture": "good",
  "eye_contact": "engaged",
  "wpm": 142,
  "filler_count": 4,
  "tip": "Lift your chin toward the camera."
}
```

| Field | Values |
| :--- | :--- |
| `posture` | `"good"` \| `"slouching"` |
| `eye_contact` | `"engaged"` \| `"looking_away"` |
| `wpm` | integer ≥ 0 |
| `filler_count` | integer ≥ 0, **cumulative for the session** |
| `tip` | string, max 12 words (parser truncates) |

### Summary (`type: "summary"`) — scorecard

Emitted once after Person 3 sends the stop signal.

```json
{
  "type": "summary",
  "overall_score": 78,
  "posture_score": 80,
  "eye_contact_score": 72,
  "pace_score": 85,
  "filler_score": 64,
  "avg_wpm": 145,
  "total_fillers": 12,
  "strengths": ["Steady pace"],
  "improvements": ["Watch filler like"]
}
```

Scores are integers 0–100. `strengths` / `improvements` are short string arrays.

### Stop signal (Person 3)

When the user hits stop, send realtime **text** exactly:

```python
SESSION_END_TEXT  # "session_end"
await session.send_realtime_input(text=SESSION_END_TEXT)
```

Do not paraphrase this string. The prompt keys off the exact text.

## Person 3 session sketch

```python
from app.gemini import (
    get_client,
    get_model_name,
    build_live_config,
    audio_blob,
    video_blob,
    ack_tool_call,
    SESSION_END_TEXT,
)
from app.utils import JsonStreamParser, parse_tool_call

client = get_client()
parser = JsonStreamParser()

async with client.aio.live.connect(
    model=get_model_name(),
    config=build_live_config(),
) as session:
    await session.send_realtime_input(audio=audio_blob(pcm_bytes))
    await session.send_realtime_input(video=video_blob(jpeg_bytes))

    async for message in session.receive():
        if message.tool_call:
            acks = []
            for fc in message.tool_call.function_calls or []:
                event = parse_tool_call(fc.name, fc.args)
                if event is not None:
                    await websocket.send_json(event.model_dump(mode="json"))
                acks.append(ack_tool_call(fc))
            if acks:
                await session.send_tool_response(function_responses=acks)
        if message.text:
            for event in parser.feed(message.text):
                await websocket.send_json(event.model_dump(mode="json"))

    await session.send_realtime_input(text=SESSION_END_TEXT)
```

`build_live_config()` sets AUDIO modality, coaching tools, and input/output transcription. Do not override `response_modalities` to TEXT.

Use a **new** `JsonStreamParser()` (or `parser.reset()`) per browser session.

## Setup and tests

```bash
cd server
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s . -p 'test_*.py' -v
```

Tests do not need an API key. Optional client check (needs `GEMINI_API_KEY`):

```bash
cd server
python3 -m app.gemini.client
```

Dependencies here: `google-genai`, `python-dotenv`, `pydantic`. FastAPI / uvicorn stay Person 3’s `requirements.txt` additions.

## Out of scope (do not expect these files from Person 1)

- `app/main.py` and `app/gemini/live_stream.py` — Person 3
- Anything under `client/` — Person 2
- Dockerfile / Render / Vercel — Person 3
