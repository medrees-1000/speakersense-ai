import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.gemini.live_stream import handle_gemini_stream

load_dotenv()

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="PostureSense AI Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "PostureSense AI Backend"}


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected to posture WebSocket gateway")
    try:
        await handle_gemini_stream(websocket)
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error in WebSocket session: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
