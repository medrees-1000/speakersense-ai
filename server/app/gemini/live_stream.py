"""FastAPI ↔ Gemini Live WebSocket proxy for posture coaching.

Browser protocol (JSON text frames):
  → {"type":"video_frame","data":"<base64 jpeg>"}
  → {"type":"session_end"}
  ← LiveTick / SessionSummary via event.model_dump(mode="json")
  ← {"type":"error","message":"..."} on fatal setup failures
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect
from google.genai import types

from app.gemini import (
    SESSION_END_TEXT,
    ack_tool_call,
    build_live_config,
    get_client,
    get_model_name,
    video_blob,
)
from app.utils import JsonStreamParser, parse_tool_call

logger = logging.getLogger(__name__)


async def _send_event(websocket: WebSocket, event: object) -> None:
    if hasattr(event, "model_dump"):
        await websocket.send_json(event.model_dump(mode="json"))
    else:
        await websocket.send_json(event)


async def _forward_browser_to_gemini(websocket: WebSocket, session) -> None:
    """Relay JPEG frames and session_end from the browser into Gemini Live."""
    async for raw in websocket.iter_text():
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Ignoring non-JSON browser message")
            continue

        msg_type = payload.get("type")
        if msg_type == "video_frame":
            data = payload.get("data") or payload.get("base64Frame")
            if not data:
                continue
            try:
                jpeg_bytes = base64.b64decode(data)
            except Exception:
                logger.warning("Invalid base64 video frame")
                continue
            await session.send_realtime_input(video=video_blob(jpeg_bytes))
        elif msg_type == "session_end":
            await session.send_realtime_input(text=SESSION_END_TEXT)
            # Keep the receive loop alive briefly so emit_summary can arrive.
            await asyncio.sleep(8.0)
            return


async def _forward_gemini_to_browser(websocket: WebSocket, session) -> None:
    """Parse tool calls / text JSON and push coaching events to the browser."""
    parser = JsonStreamParser()

    async for message in session.receive():
        if message.tool_call:
            calls = message.tool_call.function_calls or []
            logger.info("Gemini tool_call: %s", [fc.name for fc in calls])
            acks: list[types.FunctionResponse] = []
            for fc in calls:
                event = parse_tool_call(fc.name, fc.args)
                if event is None:
                    logger.warning(
                        "Tool call %s did not validate into a coaching event: %s",
                        fc.name,
                        fc.args,
                    )
                else:
                    await _send_event(websocket, event)
                acks.append(ack_tool_call(fc))
            if acks:
                await session.send_tool_response(function_responses=acks)

        text_bits: list[str] = []
        if getattr(message, "text", None):
            text_bits.append(message.text)
        server_content = getattr(message, "server_content", None)
        if server_content is not None:
            transcription = getattr(server_content, "output_transcription", None)
            if transcription is not None and getattr(transcription, "text", None):
                text_bits.append(transcription.text)
        for chunk in text_bits:
            logger.debug("Gemini text chunk: %r", chunk)
            for event in parser.feed(chunk):
                logger.info("Parsed %s event from raw text fallback", event.type)
                await _send_event(websocket, event)


async def handle_gemini_stream(client_socket: WebSocket) -> None:
    """Accept a browser WebSocket and proxy a full posture coaching session."""
    try:
        client = get_client()
    except RuntimeError as exc:
        await client_socket.send_json({"type": "error", "message": str(exc)})
        await client_socket.close()
        return

    model = get_model_name()
    config = build_live_config()

    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            browser_task = asyncio.create_task(
                _forward_browser_to_gemini(client_socket, session)
            )
            gemini_task = asyncio.create_task(
                _forward_gemini_to_browser(client_socket, session)
            )
            try:
                done, _pending = await asyncio.wait(
                    {browser_task, gemini_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in done:
                    exc = task.exception()
                    if exc and not isinstance(
                        exc,
                        (WebSocketDisconnect, asyncio.CancelledError, StopAsyncIteration),
                    ):
                        raise exc
            finally:
                for task in (browser_task, gemini_task):
                    if not task.done():
                        task.cancel()
                await asyncio.gather(browser_task, gemini_task, return_exceptions=True)
    except WebSocketDisconnect:
        logger.info("Browser disconnected from posture stream")
    except Exception as exc:
        logger.exception("Posture stream error: %s", exc)
        try:
            await client_socket.send_json(
                {"type": "error", "message": f"Stream error: {exc}"}
            )
        except Exception:
            pass