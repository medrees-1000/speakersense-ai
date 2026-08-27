## Team Roles & Task Allocation Matrix

| Role | Team Member | Primary Scope | Core Deliverables |
| :--- | :--- | :--- | :--- |
| **1. AI & Data Lead** | [Name] | `server/app/gemini/` | Prompt tuning, posture JSON schemas, frame optimization |
| **2. Frontend Lead** | [Name] | `client/src/` | Video capture, live HUD gauges, scorecard + exercises UI |
| **3. Backend & Pitch Lead** | [Name] | `server/app/main.py` & `presentation/` | FastAPI WebSockets, cloud deployment, slides |

---

### Person 1: AI & Prompt Lead

**Focus Area:** Gemini Live API setup, posture system prompts, structured data, and token efficiency.

* **`server/app/gemini/client.py`** — `google-genai` SDK + Live config
* **`server/app/gemini/prompts.py`** — posture / severity / spoken_cue / exercises schemas
* **`server/app/utils/json_parser.py`** — stream-safe JSON extraction
* **Token optimization** — ~1 FPS JPEG frames, max width 640

---

### Person 2: Frontend & UX Lead

**Focus Area:** Next.js application, canvas frame sampling, live HUD, spoken alerts, scorecard.

* **`client/src/hooks/use-webcam.ts`** — `getUserMedia` + 1 FPS JPEG sampling
* **`client/src/hooks/use-socket.ts`** — native WebSocket to `/ws/stream`
* **`client/src/components/live-hud.tsx`** — posture / severity / tip gauges + browser TTS
* **`client/src/components/scorecard.tsx`** — scores, habits, corrective exercises

---

### Person 3: Backend, Infra & Pitch Lead

**Focus Area:** FastAPI WebSocket proxy, hosting, slides.

* **`server/app/main.py` & `server/app/gemini/live_stream.py`** — browser ↔ Gemini Live
* Deploy backend (Render/Railway) + Next.js (Vercel) with `NEXT_PUBLIC_WS_URL`
* **`presentation/`** — pitch deck + demo backup video
