# Android connection

The hub runs on the laptop, because the speech model needs the laptop's graphics
card. So the laptop must be awake, running the hub, and connected to Tailscale
whenever you want to dictate from the phone.

On the laptop, publish the hub on its private Tailscale address once:

```powershell
tailscale serve --bg --https=443 8766
```

Proxy the root, not `--set-path=/tts-stt`: Tailscale strips the path it is given
before forwarding, so a `/tts-stt` mount hands the hub a request for `/` and the
hub answers `Not Found`. This mirrors the mini PC's single root proxy.

Start the hub with `HUB_BASE_URL=https://leeloo.tail97bf76.ts.net/tts-stt` in
`.env`, then confirm `https://leeloo.tail97bf76.ts.net/tts-stt/` opens in the
phone's browser with Tailscale connected. The hub itself still listens only on
loopback; Tailscale is the only way in. Do not open ports to work around this.

Use an Android dictation client that allows a **custom OpenAI-compatible base
address and model**. Candidate keyboard apps from the plan require testing;
this checkpoint does not claim a particular APK/version is compatible.

| Client setting | Value |
|---|---|
| API base address | `https://leeloo.tail97bf76.ts.net/tts-stt/v1` |
| API key | A new device key named for this phone, created in hub settings |
| Transcription model | Anything, including `whisper-1`; the hub ignores it |
| Audio | WAV, M4A, OGG, WebM, MP3, FLAC or AAC; under 25 MB |

If the app asks for a complete transcription endpoint instead of a base address,
use `https://leeloo.tail97bf76.ts.net/tts-stt/v1/audio/transcriptions`.
Enter the device key, not any other credential. A hardcoded `whisper-1` model is
fine; extra unsupported fields or a non-customizable endpoint will be rejected.

Enable the keyboard in Android's keyboard settings, switch to it, then dictate a
short sentence into a notes app. Verify punctuation, actual insertion, and that
revoking its device key prevents further transcription. Record the app version
and results before considering the phone accepted. Repeat with a different key
for the tablet. Until then, the authenticated browser tester can test dictation.
