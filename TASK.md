## 👥 Team Roles & Task Allocation Matrix

| Role | Team Member | Primary Scope | Core Deliverables |
| :--- | :--- | :--- | :--- |
| **1. AI & Data Lead** | [Name] | `server/app/gemini/` | Prompt tuning, JSON schemas, frame optimization[cite: 1] |
| **2. Frontend Lead** | [Name] | `client/src/` | Video capture, live HUD gauges, scorecard UI[cite: 1] |
| **3. Backend & Pitch Lead** | [Name] | `server/app/main.py` & `presentation/` | FastAPI WebSockets, cloud deployment, slides[cite: 1] |

---

### 🟢 Person 1: AI & Prompt Lead

**Focus Area:** Gemini Live API setup, system prompts, structured data, and token efficiency[cite: 1].

* **`server/app/gemini/client.py`**
  * Initialize `google-genai` Python SDK using `GEMINI_API_KEY` environment variables[cite: 1].
* **`server/app/gemini/prompts.py`**
  * Draft system instructions for evaluating posture, eye contact, filler word counts, and speaking pace[cite: 1].
  * Enforce strict raw JSON response schemas for real-time streaming updates[cite: 1].
* **`server/app/utils/json_parser.py`**
  * Parse incoming Gemini text chunks safely and strip out any markdown fences[cite: 1].
* **Token Optimization**
  * Tune sample rate parameters (target ~1 FPS image frames) to preserve latency and API quota limits[cite: 1].

---

### 🔵 Person 2: Frontend & UX Lead

**Focus Area:** Next.js application, Media Recorder/Canvas APIs, dynamic HUD, and scorecard page[cite: 1].

* **`client/src/hooks/use-webcam.ts`**
  * Hook up browser `getUserMedia` and HTML5 canvas frame sampling at 1 FPS[cite: 1].
* **`client/src/components/webcam-feed.tsx`**
  * Render live video stream container with canvas visual overlays[cite: 1].
* **`client/src/components/live-hud.tsx`**
  * Build dynamic UI gauges for Posture ("Good"/"Slouching"), Eye Contact, WPM, and Filler Words[cite: 1].
* **`client/src/app/summary/page.tsx` & `scorecard.tsx`**
  * Design final post-presentation evaluation dashboard displaying overall delivery scores[cite: 1].

---

### 🟣 Person 3: Backend, Infra & Pitch Lead

**Focus Area:** FastAPI WebSocket proxy server, multi-platform hosting, slides, and stage demo strategy[cite: 1].

* **`server/app/main.py` & `server/app/gemini/live_stream.py`**
  * Build FastAPI WebSocket endpoints to handle bidirectional audio/video streaming between browser and Gemini Live API[cite: 1].
* **Deployment Setup**
  * Write production `Dockerfile` and configure Render/Railway hosting for backend WebSockets[cite: 1].
  * Deploy Next.js frontend to Vercel and set `NEXT_PUBLIC_WS_SERVER_URL` environment variables[cite: 1].
* **`presentation/`**
  * Build hackathon pitch deck (`slide-deck.pdf`) detailing problem, tech stack, and scalability[cite: 1].
  * Record pre-rendered application backup video (`demo-backup.mp4`) for fallback during stage presentation[cite: 1].