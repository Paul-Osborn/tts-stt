# Spec — Version 1 Multi-Provider Speech Hub

## Outcome

A private, self-hosted FastAPI speech hub on Minisforum. It gives the owner's Android, tablet,
and Windows clients OpenAI-compatible transcription and speech endpoints under the existing
`/tts-stt` mount, plus a Voice Control Center and mounted tester. The hub, its routing,
settings, credentials, and audit records stay on the owner's server; selected external providers
receive submitted audio or text to process. This is private infrastructure, not end-to-end local
or private processing.

## Version 1 scope

- A shared secure hub core and versioned compatibility contract for `POST /v1/audio/transcriptions`,
  `POST /v1/audio/speech`, `GET /v1/models`, and `GET /health`.
- Audited adapters for Gemini, OpenRouter, and one vetted generic OpenAI-compatible audio provider.
  A Control Center can add credentials and enable a verified profile only for those code-defined
  provider types. A new/custom API requires a small adapter change, conformance proof, and a
  separate approval; arbitrary pasted endpoint URLs are never accepted.
- One distinct, revocable hub credential per Android/tablet/Windows client. It is shown once on
  issue, stored durably as a verifier only, cannot be exported from the browser, and supports
  revoke/replace. It is never a provider credential.
- Voice Control Center access through Google sign-in restricted to the configured owner subject
  and email allowlist, plus a separately protected emergency recovery password and process.
  The actual owner account and recovery values are setup-time secrets, never documentation.
- Provider profiles are allowlisted and live-proven. The UI shows the chosen provider/profile and
  its processing disclosure. There is no arbitrary model/service selection, silent substitution,
  or automatic cross-provider fallback.
- Gemini is the first vertical proof: secure core, one Gemini STT profile, one Gemini TTS profile,
  mounted tester, and one real device. OpenRouter and generic-compatible profiles follow only
  after the same profile-by-profile proof gates.

## Endpoint behavior

- Faithful transcription is the default. Light Cleanup is tester-only and deferred until endpoint
  evidence supports it.
- Explicit valid client values override server defaults. Unsupported values fail clearly; they do
  not silently select another model or provider.
- The canonical external base URL comes from fixed deployment configuration, never request
  headers. Exactly one approved loopback/proxy mounted path is supported.

## Security, credentials, and retention contract

- No public exposure, Tailscale Funnel, or unapproved Tailscale/Caddy/server-route change. The
  mounted `/tts-stt` contract remains; routing changes require the shared-server process.
- Root secrets stay only in local `.env`: Gemini key, Google OAuth secret, provider-vault root or
  encryption key, recovery secret, and equivalent root credentials. No secret enters source,
  commits, logs, backups, or error messages.
- Added provider credentials live only in a restricted server-side provider vault. Each value uses
  atomic, provider-bound authenticated encryption under the server-held root, is never shown after
  entry, and is excluded from plaintext logs and backups. The implementation must include root
  custody, rotation, recovery, and loss runbooks; loss of the vault root means stored provider
  credentials cannot be recovered and must be re-entered.
- Google sign-in uses state, nonce, and PKCE; the server checks the fixed Google subject/email
  allowlist. Sessions are secure, CSRF-protected, and require recent reauthentication for
  sensitive settings, credential, and recovery actions.
- Adapter destinations use fixed canonical provider origins, reject redirects, and validate every
  outbound destination. Settings mutate only through an authenticated transactional service with
  out-of-band mutation detection.
- Audit events are content-free and have a defined retention period. Never retain transcript or
  audio history, raw request headers, secrets, provider error bodies, or user content. Temporary
  files, logs, crash material, proxy-failure injection, and stale-cleanup proof are ephemeral.
- Gemini is intended for the API Free Tier only: do not link billing for this API project. Enforce
  hard request/resource limits rather than an invented dollar cap. Selected models and Free Tier
  availability must be verified at setup time. Google Free Tier handling follows Google's current
  terms; the hub promises no server-side content history, not control of provider retention.
- OpenRouter is first class for existing credits and qualifying free models. Capability, credit,
  and free-status evidence is owner-triggered, timestamped, and never guessed or auto-probed on
  page load.

## Compatibility and proof gates

- Maintain a versioned hub compatibility contract and semantic adapter conformance suite.
- Each enabled profile passes configuration validation, fixed-origin checks, authenticated tester
  proof, endpoint contract tests, content-free audit checks, and real-device acceptance before it
  can be offered to a client.
- Test the service through the mounted path, not only at root. Prove ephemeral cleanup with stale
  temporary/crash/log and proxy-failure-injection cases.

## Phased delivery

1. **Secure core and Gemini proof:** compatibility contract, credential lifecycle, Control Center
   protection, provider vault, audit/retention controls, one Gemini STT and one Gemini TTS profile,
   mounted tester, and one real device.
2. **OpenRouter proof:** enable independently after the same adapter, profile, and real-device gates.
3. **Generic-compatible proof:** enable independently after the same gates.

## Deferred / out of scope

- Application code, provider account calls, Google OAuth configuration, deployment, and shared
  server routing changes until a separately approved implementation phase.
- Custom Android IME development, multi-user/SaaS billing, heavy local speech models, arbitrary
  custom provider URLs, automatic provider fallback, transcript/audio history, and browser export
  of client or provider credentials.

## Setup-time verification items

- Owner Google subject/email, recovery procedure, canonical base URL, provider profile capability,
  exact Gemini models and Free Tier availability, OpenRouter credit/free status, and real-device
  results are verified during setup; none are assumed by this specification.

## Acceptance for implementation authorization

The first implementation phase is authorized only after the owner approves this spec and the
Gemini vertical slice has evidence for every gate above. Provider expansions require their own
profile evidence; passing Gemini does not approve or imply other providers.
