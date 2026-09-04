# Spec — Core STT & TTS Hub with Gemini Integration

> **How to use this template:** Fill it in and agree on it **before** writing code — this is the thing to review,
> not the implementation. Keep it updated as decisions change; it's the source of truth.

## Outcome
A self-hosted, lightweight service hub running on the Minisforum local server (or local Windows machine) that exposes standard OpenAI-compatible audio endpoints (`/v1/audio/transcriptions` and `/v1/audio/speech`). Speech-to-text is powered by Gemini Flash with intelligent formatting and punctuation; text-to-speech is powered by Gemini Flash TTS with selectable natural voices. Android devices can immediately use it for voice typing via open-source keyboard APKs (such as Whisper IME), Windows PCs can use it via a desktop hotkey tool, and any browser can access the built-in testing dashboard.

## In scope
- **Environment & Dependencies:** `requirements.txt` with pinned versions (`fastapi`, `uvicorn`, `python-multipart`, `google-genai`, `python-dotenv`, `pytest`, `httpx`).
- **Configuration & Secrets:** `.env.example` defining `GEMINI_API_KEY`, server host/port, default TTS voice, and prompt formatting preferences.
- **Gemini Service Integration:** `app/gemini_service.py` using official `google-genai` SDK for audio transcription and speech synthesis.
- **OpenAI-Compatible Audio API:**
  - `POST /v1/audio/transcriptions`: Accepts multipart form audio, converts to clean punctuated text, returns `{ "text": "..." }`.
  - `POST /v1/audio/speech`: Accepts JSON with model, voice, and input text; streams back raw audio bytes.
  - `GET /v1/models`: Returns list of supported STT and TTS models.
  - `GET /health`: Health check endpoint.
- **Web Dashboard:** `app/static/index.html` allowing the user to test microphone recording, view transcription, test TTS voices, and verify the server status.
- **Desktop Dictation Client:** `client/desktop.py` (Windows hotkey listener for system-wide dictation) and `client/README.md`.
- **Android Setup Documentation:** `docs/android_setup.md` guide on configuring Whisper IME / Sayboard APK to connect to the hub.
- **Automated Tests:** `tests/test_api.py` validating API responses, schema adherence, and error handling.

## Out of scope
- Building custom native Android APK from source (using existing open-source keyboards).
- Heavy local neural model binaries (Kokoro, Whisper local weights) since user selected Gemini Pro / API approach.
- Multi-user authentication or public SaaS billing.

## Constraints
- **Zero hardcoded secrets:** `GEMINI_API_KEY` loaded exclusively from environment / `.env`.
- **OpenAI API Standard:** Endpoints must strictly match OpenAI specification so off-the-shelf mobile keyboards work seamlessly without requiring custom client apps.
- **Fast turnaround:** Asynchronous I/O with minimal streaming latency.
- **Windows PowerShell 5.1 compatibility:** All commands provided must be single-command PowerShell syntax without bashisms or `&&`.

## Prior decisions to respect
- Use Google Gemini API (user's Gemini key) for STT and TTS instead of heavy local models.
- Ditch Kokoro in favor of Gemini Flash TTS.
- Hub runs on Minisforum (or local Windows machine) and connects over LAN / Tailscale.

## Plan (files & steps)
1. `requirements.txt` — define and pin core dependencies.
2. `.env.example` — configuration template.
3. `app/config.py` — environment settings and prompt configurations.
4. `app/gemini_service.py` — Gemini client interactions (transcribe with formatting, generate speech).
5. `app/main.py` — FastAPI application routing `/v1/audio/transcriptions`, `/v1/audio/speech`, `/v1/models`, `/health`, and static files.
6. `app/static/index.html` — browser test UI.
7. `client/desktop.py` — Windows hotkey dictation utility.
8. `docs/android_setup.md` — Android connection guide for Whisper IME.
9. `tests/test_api.py` — unit and endpoint tests.
10. `README.md` — human-friendly project guide.

## How we'll verify it works
1. Run automated test suite: `pytest` passing all tests.
2. Start server locally: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
3. Test `/v1/audio/transcriptions` with a sample audio file to ensure formatted text is returned.
4. Test `/v1/audio/speech` with sample text to ensure valid audio bytes are returned.
5. Open `http://localhost:8000` in browser to test the web interface.

## Open questions
- None for milestone 1; ready for implementation upon approval.
