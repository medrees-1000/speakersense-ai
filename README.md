# PostureSense AI

Real-time posture coach powered by Gemini Live. Watches your webcam, speaks up
when your posture slips, then delivers a session report with corrective exercises.

## Stack

- **Client** — Next.js (`client/`) live HUD + scorecard
- **Server** — FastAPI WebSocket gateway (`server/`) → Gemini Live

See [server/README.md](server/README.md) for the JSON contract and media knobs.

## Quick start

```bash
# Backend
cd server
cp .env.example .env   # add GEMINI_API_KEY
python3 -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd client
npm install
npm run dev
```

Open http://localhost:3000, start a session, and allow camera access.
