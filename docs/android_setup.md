# Android connection

First complete the private server deployment and confirm the tester works at
`https://gitserver.tail97bf76.ts.net/tts-stt/` from the phone's browser with
Tailscale connected. The phone cannot reach a server running only on laptop
localhost. Do not open ports to work around this.

Use an Android dictation client that allows a **custom OpenAI-compatible base
address and model**. Candidate keyboard apps from the plan require testing;
this checkpoint does not claim a particular APK/version is compatible.

| Client setting | Value |
|---|---|
| API base address | `https://gitserver.tail97bf76.ts.net/tts-stt/v1` |
| API key | A new device key named for this phone, created in hub settings |
| Transcription model | Anything, including `whisper-1`; the hub ignores it |
| Audio | WAV, M4A, OGG, WebM, MP3, FLAC or AAC; under 25 MB |

If the app asks for a complete transcription endpoint instead of a base address,
use `https://gitserver.tail97bf76.ts.net/tts-stt/v1/audio/transcriptions`.
Enter the device key, not any other credential. A hardcoded `whisper-1` model is
fine; extra unsupported fields or a non-customizable endpoint will be rejected.

Enable the keyboard in Android's keyboard settings, switch to it, then dictate a
short sentence into a notes app. Verify punctuation, actual insertion, and that
revoking its device key prevents further transcription. Record the app version
and results before considering the phone accepted. Repeat with a different key
for the tablet. Until then, the authenticated browser tester can test dictation.

The hub runs on the laptop's graphics card, so the laptop must be awake and on
Tailscale for the phone to dictate.
