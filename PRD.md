# Project brief / PRD — tts-stt

> **What this is:** The project-level brief — what we're building and why. Created at project start and kept updated as decisions evolve.

## Problem / why
Google Voice Typing is frustratingly inaccurate, lacks smart contextual formatting (handling punctuation, filler words, technical jargon), and relies entirely on closed, unowned services. The owner wants a private, responsive, self-hosted Speech-to-Text (STT) and Text-to-Speech (TTS) system they own and control, capable of replacing Google Voice Typing across their Android phone, Android tablet, and desktop PC.

## Goal / outcome
A self-hosted STT and TTS server hub running on the local Minisforum server that exposes OpenAI-compatible audio endpoints backed by Google Gemini models, enabling seamless system-wide voice typing on mobile devices (via polished open-source keyboard APKs) and desktop PCs.

## Users / context
The owner across their primary personal devices (Android phone, Android tablet, and Windows desktop PC), communicating with the local Minisforum server over local Wi-Fi or secure mesh VPN (Tailscale).

## Scope
- **In:**
  - Lightweight Python FastAPI hub running on the Minisforum server.
  - OpenAI-compatible endpoints: `POST /v1/audio/transcriptions` and `POST /v1/audio/speech`.
  - Gemini API integration using `google-genai` SDK (Gemini Flash for transcription + smart punctuation/grammar formatting; Gemini 3.1 Flash TTS for voice synthesis).
  - Built-in web dashboard on the hub for testing audio, previewing voices, and managing settings.
  - Windows desktop voice typing hotkey utility (hold key -> record -> paste text).
  - Setup and configuration guide for Android clients using open-source keyboards (e.g., Whisper IME / Sayboard).
- **Out (for now):**
  - Building a custom Android IME keyboard from scratch (using existing polished open-source APKs instead).
  - Multi-user authentication or public SaaS billing infrastructure.
  - Heavy local neural model installations on the Minisforum server (utilizing Gemini cloud API via owner's key to keep the server ultra-lightweight).

## Requirements
- Expose `POST /v1/audio/transcriptions` conforming to OpenAI Audio API spec (multipart audio in, JSON `{ "text": "..." }` out).
- Expose `POST /v1/audio/speech` conforming to OpenAI Audio API spec (text and voice options in, audio byte stream out).
- Use Gemini models via `google-genai` SDK with `GEMINI_API_KEY`.
- Provide system prompts for STT to cleanly strip filler words ("um", "uh"), insert proper punctuation, and respect formatting commands without altering the speaker's meaning.
- Provide a simple web UI served by the hub to test microphone recording, transcription, and TTS playback.
- Provide a lightweight Windows client script for hotkey-based dictation.

- **Security / privacy:** `GEMINI_API_KEY` stored exclusively in local `.env` (never committed to git). Hub exposed remotely strictly via private `tailscale serve --https=443 --set-path="/tts-stt"` (`https://<node>.<tailnet>.ts.net/tts-stt`) with Tailscale Funnel disabled (no public internet exposure). Host & origin guard active.
- **Performance / limits:** Sub-second to 1.5s turnaround for dictation snippets. Server memory footprint under 200 MB RAM and negligible CPU when idle.
- **Platform:** Server runs on Windows or Linux / Docker (Python 3.11+); mobile clients on Android.

## Constraints / decisions already made
- **Stack:** Python 3.11+, FastAPI, Uvicorn, `google-genai`, `python-dotenv`.
- **API Standard:** OpenAI Audio API compatibility so off-the-shelf clients (Whisper IME, etc.) work out-of-the-box without custom mobile app builds.
- **Engines:** Gemini Flash for STT / text cleanup; Gemini Flash TTS for voice generation (no Kokoro).

## Success criteria (how we'll know it works)
- The FastAPI hub starts, passes automated endpoint tests, and transcribes test audio files into formatted text.
- An Android device with Whisper IME connects to the hub and types transcribed text into any app when pressing the mic button.
- The desktop hotkey tool records voice on keypress and automatically pastes text into the focused window.
- The web interface allows testing audio input and playing back synthesized Gemini speech.

## Risks / open questions
- *Mobile network connectivity outside home Wi-Fi:* Solved by running Tailscale on the Minisforum and mobile devices.
- *Audio format compatibility across Android audio recorders:* Ensure hub handles `wav`, `mp3`, `m4a`, `ogg`, `webm`, and `flac` cleanly.

## Milestones
1. **Repository & Governance Setup:** Initialize git, configure rule templates, create PRD, and make initial commit on branch.
2. **Core Server Hub:** Build FastAPI server with OpenAI-compatible STT and TTS endpoints powered by `google-genai`.
3. **Web Dashboard:** Add browser-based testing UI for microphone input and TTS playback.
4. **Desktop Dictation Client:** Build lightweight Windows hotkey listener for PC voice typing.
5. **Android Integration Guide & Verification:** Provide setup instructions and test with mobile open-source keyboard APK.
