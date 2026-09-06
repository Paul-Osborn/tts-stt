# Project brief / PRD — tts-stt

> **What this is:** The project-level brief — what we're building and why. Created at project start and kept updated as decisions evolve.

## Problem / why
Google Voice Typing is frustratingly inaccurate, lacks smart contextual formatting (handling punctuation, filler words, technical jargon), and relies entirely on closed, unowned services. The owner wants a private, responsive, self-hosted Speech-to-Text (STT) and Text-to-Speech (TTS) system they own and control, capable of replacing Google Voice Typing across their Android phone, Android tablet, and desktop PC.

## Goal / outcome
A self-hosted, multi-provider STT and TTS hub on the local Minisforum server. It exposes OpenAI-compatible audio endpoints for mobile devices (via polished open-source keyboard APKs) and desktop PCs while keeping hub control, routing, settings, and credential management local. Selected external providers receive submitted audio/text to process; this is not end-to-end local processing.

## Users / context
The owner across their primary personal devices (Android phone, Android tablet, and Windows desktop PC), communicating with the local Minisforum server over local Wi-Fi or secure mesh VPN (Tailscale).

## Scope
- **In:**
  - Lightweight Python FastAPI hub running on the Minisforum server.
  - OpenAI-compatible endpoints: `POST /v1/audio/transcriptions` and `POST /v1/audio/speech`.
  - Audited Gemini, OpenRouter, and generic OpenAI-compatible audio-provider adapters with allowlisted, live-proven profiles.
  - Voice Control Center for owner-only settings, provider profiles, an encrypted provider vault, and a mounted tester.
  - Distinct revocable hub credentials for each Android/tablet/Windows client.
  - Windows desktop voice typing hotkey utility (hold key -> record -> paste text).
  - Setup and configuration guide for Android clients using open-source keyboards (e.g., Whisper IME / Sayboard).
- **Out (for now):**
  - Building a custom Android IME keyboard from scratch (using existing polished open-source APKs instead).
  - Multi-user authentication, public SaaS billing, arbitrary custom provider URLs, or automatic cross-provider fallback.
  - Heavy local neural model installations on the Minisforum server (utilizing Gemini cloud API via owner's key to keep the server ultra-lightweight).

## Requirements
- Expose `POST /v1/audio/transcriptions` conforming to OpenAI Audio API spec (multipart audio in, JSON `{ "text": "..." }` out).
- Expose `POST /v1/audio/speech` conforming to OpenAI Audio API spec (text and voice options in, audio byte stream out).
- Start with Gemini, then independently enable OpenRouter and generic-compatible provider profiles only after equivalent proof.
- Keep faithful transcription as the endpoint default; Light Cleanup remains tester-only/deferred pending evidence.
- Provide a simple web UI served by the hub to test microphone recording, transcription, and TTS playback.
- Provide a lightweight Windows client script for hotkey-based dictation.

- **Security / privacy:** Root secrets (Gemini, Google OAuth, vault root/encryption key, recovery) stay only in local `.env`; added provider credentials stay only in a restricted encrypted server-side provider vault and are never shown after entry. Hub access is private `tailscale serve --https=443 --set-path="/tts-stt"` with Funnel disabled; host/origin, fixed outbound destinations, owner-only Google sign-in, secure sessions, and recovery protection are required.
- **Performance / limits:** Sub-second to 1.5s turnaround for dictation snippets. Server memory footprint under 200 MB RAM and negligible CPU when idle.
- **Platform:** Server runs on Windows or Linux / Docker (Python 3.11+); mobile clients on Android.

## Constraints / decisions already made
- **Stack:** Python 3.11+, FastAPI, Uvicorn, `google-genai`, `python-dotenv`.
- **API Standard:** OpenAI Audio API compatibility so off-the-shelf clients (Whisper IME, etc.) work out-of-the-box without custom mobile app builds.
- **Providers:** Gemini is the first proof; OpenRouter and generic-compatible providers are core V1 architecture but activate only after their own verified profiles. Gemini API use is Free Tier-only with hard resource limits; exact model/free-tier availability is setup-time verification.

## Success criteria (how we'll know it works)
- The first Gemini STT/TTS profiles pass compatibility, security, mounted-tester, ephemeral-cleanup, and real-device acceptance evidence.
- Each later enabled provider profile independently passes those same gates before it reaches a client.
- The desktop hotkey tool records voice on keypress and automatically pastes text into the focused window.
- The web interface allows testing audio input and playing back synthesized Gemini speech.

## Risks / open questions
- *Mobile network connectivity outside home Wi-Fi:* Solved by running Tailscale on the Minisforum and mobile devices.
- *Audio format compatibility across Android audio recorders:* Ensure hub handles `wav`, `mp3`, `m4a`, `ogg`, `webm`, and `flac` cleanly.

## Milestones
1. **Repository & Governance Setup:** Initialize git, configure rule templates, create PRD, and make initial commit on branch.
2. **Secure Hub Core & Gemini Proof:** Build the compatibility contract, protected Control Center, credential/vault lifecycle, one Gemini STT/TTS vertical slice, mounted tester, and real-device proof.
3. **Provider Expansions:** Enable OpenRouter, then generic-compatible profiles independently after equivalent proof.
4. **Desktop Dictation Client:** Build lightweight Windows hotkey listener for PC voice typing.
5. **Android Integration Guide & Verification:** Provide setup instructions and test with mobile open-source keyboard APK.
