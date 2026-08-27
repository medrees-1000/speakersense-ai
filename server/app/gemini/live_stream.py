import json
import os
from fastapi import WebSocket
from google import genai
from app.gemini.prompts import SYSTEM_PROMPT

async def handle_gemini_stream(client_socket: WebSocket):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        return
    ai = genai.Client(api_key=api_key)
    

    async with ai.aio.live.connect(
        model="gemini-live-2.5-flash-preview",
        config={
            "response_modalities": ["TEXT"],
            "SYSTEM_PROMPT": SYSTEM_PROMPT,
        }
    ) as session:
        
        async for message in client_socket.iter_text():
            payload = json.loads(message)
            msg_type = payload.get("type")
            
            if msg_type == "video_frame":
                await session.send(
                    input={"data": payload["base64Frame"], "mime_type": "image/jpeg"},
                    end_of_turn=False
                )
            elif msg_type == "audio_chunk":
                await session.send(
                    input={"data": payload["base64Pcm"], "mime_type": "audio/pcm; rate=16000"},
                    end_of_turn=False
                )
                
            async for response in session.receive():
                if response.text:
                    await client_socket.send_text(json.dumps({
                        "type": "HUD_UPDATE",
                        "data": response.text
                    }))
