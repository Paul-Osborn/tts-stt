# Project brief / PRD — tts-stt

> **What this is:** The project-level brief — what we're building and why. Created at project start and kept updated as decisions evolve.

## Problem / why
Google Voice Typing cuts the owner off before he has finished speaking and does not punctuate
what it hears. Both come from the same design: it transcribes a live stream and decides for
itself when the speaker has stopped. The owner wants dictation that waits until he is finished,
punctuates properly, and belongs to him rather than to a closed service.

## Goal / outcome
A private speech-to-text hub that transcribes finished recordings with a local Whisper model on
the owner's laptop GPU. It exposes the OpenAI-compatible transcription endpoint that off-the-shelf
Android dictation keyboards already speak, so the phone, the tablet and the Windows PC all dictate
into it. No audio, text or credential leaves the machine.

## Users / context
The owner across their own devices (Android phone, Android tablet, Windows laptop), reaching the
hub over the Tailscale private mesh from home or away.

## Scope
- **In:**
  - Python FastAPI hub running on the owner's laptop, mounted privately at `/tts-stt`.
  - `POST /v1/audio/transcriptions`, OpenAI-compatible, so existing keyboards work unchanged.
  - Local Whisper `large-v3-turbo` on the laptop's RTX 3060, loaded once and kept resident.
  - Owner-only Control Center for issuing and revoking a distinct key per device.
  - Windows desktop voice typing hotkey utility (hold key -> record -> paste text).
  - Setup guide for Android clients using open-source keyboards (Whisper IME / Sayboard).
- **Out (for now):**
  - Text-to-speech. Dropped 2026-09-08; may return later as a local model.
  - Any cloud speech provider, provider vault, or outbound network call.
  - Building a custom Android keyboard from scratch.
  - Multi-user authentication, public hosting, billing.

## Requirements
- Expose `POST /v1/audio/transcriptions` conforming to the OpenAI Audio API (multipart audio in,
  JSON `{ "text": "..." }` out). The `model` field is accepted and ignored — keyboards hardcode
  `whisper-1` and there is one local engine.
- Transcribe the whole recording. Nothing may decide on the owner's behalf that he has stopped
  speaking.
- Keep faithful transcription as the endpoint default; no rewriting or cleanup of the words.
- Serve a simple web page for testing microphone recording and transcription.
- Provide a lightweight Windows client script for hotkey-based dictation.

- **Security / privacy:** The hub makes no outbound request of any kind. The root encryption key,
  Google OAuth details and recovery verifier stay only in the local `.env`. Access is private
  Tailscale with Funnel disabled; host/origin guard, owner-only Google sign-in, secure sessions
  and per-device revocable keys are required. No audio or transcript is ever written to disk.
- **Performance / limits:** Model load ~5s once at startup; roughly one second to transcribe a
  short clip on the GPU. Uploads capped at 25 MB. The model occupies GPU memory while the hub
  runs, so the 200 MB idle-RAM cap from the cloud design no longer applies and has been removed.
- **Platform:** Hub runs on Windows with an NVIDIA GPU and CUDA (Python 3.11+); clients on
  Android and Windows.

## Constraints / decisions already made
- **Stack:** Python 3.11+, FastAPI, Uvicorn, `faster-whisper`/CTranslate2, `python-dotenv`.
- **API Standard:** OpenAI Audio API compatibility so off-the-shelf clients work out of the box.
- **Where the compute runs:** the laptop GPU, not the always-on mini PC. The GPU fits the largest
  Whisper model, and accuracy is the whole point of the change. The accepted cost is that
  dictation is unavailable while the laptop is asleep. Reasoning in `docs/local-stt-direction.md`.
- **No cloud provider.** Removed 2026-09-08 along with the encrypted provider vault, the free-tier
  gate and the request quota, none of which have anything left to protect.

## Success criteria (how we'll know it works)
- A real recording of the owner speaking comes back complete, verbatim and correctly punctuated —
  not a synthetic test voice, which has no prosody to punctuate from.
- Dictation into the Android keyboard works from home and away over Tailscale.
- The desktop hotkey tool records on keypress and pastes text into the focused window.
- Nothing in normal operation opens an outbound connection.

## Risks / open questions
- *The laptop must be awake.* A sleeping laptop cannot be woken over the network. A week of real
  use decides whether this bites; the fallback is a smaller model on the mini PC.
- *Whether Google owner sign-in is still warranted* now that there is no spendable key behind it.
  Kept for now; the real wall is Tailscale plus revocable device keys.
- *Which Android keyboard to standardise on.* None tested yet.
- *Audio format compatibility across Android recorders:* `wav`, `mp3`, `m4a`, `ogg`, `webm`,
  `flac` and `aac` are accepted.

## Milestones
1. **Repository & Governance Setup:** done.
2. **Secure Hub Core:** done — contract, Control Center, device key lifecycle, mounted tester.
3. **Local GPU engine:** done — proven on real audio, wired into the endpoint.
4. **Desktop Dictation Client:** built; physical paste still unverified.
5. **Android Integration Guide & Verification:** guide written; real-device acceptance pending.
