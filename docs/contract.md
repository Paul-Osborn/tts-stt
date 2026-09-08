# Audio contract 1.0

All paths below are relative to `/tts-stt`. A device uses `Authorization: Bearer
<device-key>`. Owner browser sessions use a CSRF header on writes. Device keys
cannot manage providers or other devices. Host and Origin must match the single
configured base address. Requests with no Origin are allowed for native clients;
they still require a key.

| Endpoint | Supported request | Result |
|---|---|---|
| `GET /health` | No credentials required | Status and contract version; does not probe Google |
| `GET /v1/models` | Device key or owner session | Explicit Gemini model IDs |
| `POST /v1/audio/transcriptions` | Multipart `file`, optional `model=gemini-2.5-flash`, two-letter `language`, `response_format=json` or `text` | `{ "text": "..." }` or plain text |
| `POST /v1/audio/speech` | JSON `input`, optional `model=gemini-2.5-flash-preview-tts`, `voice=Kore`, `response_format=wav` or `pcm`, `speed=1` | Mono signed 16-bit little-endian PCM at 24 kHz, optionally wrapped as WAV |

Voices: Kore, Puck, Charon, Fenrir, Aoede. Transcription extensions: WAV, MP3,
M4A, OGG, FLAC, WebM, AAC. Gemini is responsible for decoding and rejecting invalid
audio; file extensions are allowlisted, not proof of valid audio.

Unsupported fields, model aliases (including `whisper-1`/`tts-1`), voices, formats,
and speeds fail explicitly. This is a documented subset of the OpenAI audio wire
format, not complete compatibility with every client. MP3-only or fixed-model
clients cannot use this version. Use the explicit model selector in your client.

Error shape: `{ "error": { "message": "...", "type": "hub_error", "code": 400 } }`.
400 means unsupported/invalid input; 401 sign in/key required; 403 host/origin or
owner rejection; 413 upload too large; 429 local/provider limit; 502 provider
failure; 503 setup/state issue; 504 provider timeout. Provider error bodies are
never relayed. No automatic retries can cause duplicate charges.

Contract tests prove adapter payloads, mounted routes, rejected redirects, error
redaction and state protection using simulated responses. They do not prove
Gemini semantic accuracy, actual account quota or device compatibility. Client
profiles remain provisional until owner testing is recorded.

References checked during implementation:
- [Google generateContent REST API](https://ai.google.dev/api/generate-content)
- [Google speech generation](https://ai.google.dev/gemini-api/docs/speech-generation)
- [Google audio input](https://ai.google.dev/gemini-api/docs/audio)
- [Google pricing and Free Tier](https://ai.google.dev/gemini-api/docs/pricing)

Google lists Free Tier pricing for the selected models; actual key/project access
must be checked at setup. The hub cannot inspect whether billing is enabled.
