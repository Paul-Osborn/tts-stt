# Spec — local speech-to-text hub

Supersedes the multi-provider Version 1 specification, which is dead. The owner replaced the
cloud provider with a local model on 2026-09-08; the reasoning is in
`docs/local-stt-direction.md` and the history is in `WORKLOG.md`.

## Outcome

A private FastAPI hub that transcribes finished recordings with a local Whisper model on the
owner's laptop GPU, mounted at `/tts-stt` and reachable over Tailscale. It gives the owner's
Android, tablet and Windows clients the OpenAI-compatible transcription endpoint they already
speak, plus an owner-only control page and a browser tester. Nothing leaves the machine.

## Scope

- `POST /v1/audio/transcriptions`, `GET /v1/models`, `GET /health` under the existing mount.
- Whisper `large-v3-turbo` through faster-whisper/CTranslate2 on the RTX 3060, loaded once at
  startup and kept resident. Transcription runs off the request thread.
- One distinct, revocable hub credential per client. Shown once on issue, stored as a verifier
  only, cannot be exported from the browser.
- Owner control page behind Google sign-in restricted to the configured subject and email, with
  a separately protected recovery password.
- Browser tester for recording and transcribing.

## Endpoint behavior

- Faithful transcription. No cleanup, rewriting or summarising.
- The whole recording is transcribed. Nothing decides the speaker has finished.
- The `model` field is accepted and ignored — keyboards hardcode `whisper-1` and there is one
  engine. Unsupported response formats and unknown fields still fail clearly.
- One transcription at a time; a concurrent request is refused, not queued.
- Uploads capped at 25 MB.
- The canonical external base URL comes from fixed deployment configuration, never request
  headers. Exactly one approved loopback/proxy mounted path is supported.

## Security and retention contract

- **No outbound network call.** Adding one is a change to this spec, not a pull request.
- No public exposure, Tailscale Funnel, or unapproved Tailscale/Caddy/server-route change.
- Root secrets stay only in local `.env`: the state store's encryption key, the Google OAuth
  secret and the recovery verifier. No secret enters source, commits, logs, backups or errors.
- Google sign-in uses state, nonce and PKCE and checks the fixed subject/email allowlist.
  Sessions are secure, CSRF-protected, and require recent reauthentication for device changes.
- Audio is transcribed in memory and never written to disk, including by the engine. Audit
  events are content-free and expire after seven days. No transcript or audio history.
- Host and Origin are validated against the single configured base address.

## Proof gates

- Contract tests run without a GPU using a stand-in engine: mounted routes, authentication,
  revocation, upload bounds, error redaction, state tamper detection.
- `python -m app.whisper <file>` proves the real engine on real audio.
- Real-device acceptance — phone dictation over Tailscale, Windows paste into a focused window —
  is verified on the actual devices before a client is called accepted.

## Deferred / out of scope

- Text-to-speech. May return later as a local model.
- Any cloud provider, provider vault, or custom provider URL.
- Custom Android keyboard development, multi-user, billing, transcript history.
- Moving the model to the mini PC. Reconsider only if the sleeping-laptop problem bites in a
  week of real use.

## Known limitation

The hub is unavailable while the laptop is asleep. Accepted by the owner as the price of the
larger, more accurate model.
