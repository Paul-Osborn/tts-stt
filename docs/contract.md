# Audio contract 1.0

All paths below are relative to `/tts-stt`. A device uses `Authorization: Bearer
<device-key>`. Owner browser sessions use a CSRF header on writes. Device keys
cannot manage other devices. Host and Origin must match the single configured base
address. Requests with no Origin are allowed for native clients; they still require
a key.

| Endpoint | Supported request | Result |
|---|---|---|
| `GET /health` | No credentials required | Status and contract version |
| `GET /v1/models` | Device key or owner session | The one local model ID |
| `POST /v1/audio/transcriptions` | Multipart `file`, optional `model` (ignored), two-letter `language`, `response_format=json` or `text` | `{ "text": "..." }` or plain text |

Transcription happens on this machine with Whisper `large-v3-turbo` through
faster-whisper. The hub makes no outbound network request.

Transcription extensions: WAV, MP3, M4A, OGG, FLAC, WebM, AAC. The extension is
allowlisted, not proof of valid audio; the decoder rejects the rest.

The `model` field is accepted and ignored, so clients that hardcode `whisper-1`
work unchanged. There is exactly one engine to route to. Unsupported fields and
response formats still fail explicitly. This is a documented subset of the OpenAI
audio wire format, not complete compatibility with every client. There is no
`/v1/audio/speech`; text-to-speech was dropped.

Silence detection trims leading and trailing silence, and the decoder is told not
to condition on previous text, which is what stops Whisper repeating itself on a
long pause. Nothing decides that you have stopped speaking — the recording is
transcribed whole.

Error shape: `{ "error": { "message": "...", "type": "hub_error", "code": 400 } }`.
400 means unsupported/invalid input; 401 sign in/key required; 403 host/origin or
owner rejection; 408 upload took too long; 413 upload too large; 429 another
recording is already being transcribed; 502 the engine could not transcribe;
503 setup/state issue. Engine internals are never relayed.

Contract tests prove mounted routes, authentication, revocation, upload bounds,
error redaction and state protection using a stand-in engine, so they run without
a graphics card. They do not prove transcription accuracy or device compatibility;
`python -m app.whisper <file>` checks the real engine. Client profiles remain
provisional until owner testing is recorded.
