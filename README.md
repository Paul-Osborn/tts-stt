# Speech Hub

A small private speech hub: dictate in the browser or Windows, and turn text into
spoken audio. Gemini processes submitted content; this hub saves no recordings or
transcripts. Gemini is the implemented provider. OpenRouter and other providers
remain planned and disabled pending their own live acceptance.

## Start on this Windows PC

Open PowerShell in this project folder. Run each command separately:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.manage init
```

The setup command asks for a recovery password and creates the private `.env`
settings file. Open that file locally, add `GEMINI_API_KEY`, and set
`GEMINI_FREE_TIER_CONFIRMED=yes` only after checking that the key’s Google API
project has **billing disabled**. Never paste keys into chat.

```powershell
.\.venv\Scripts\python.exe -m app.manage issue "Browser tester"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8766 --no-access-log
```

Open [the local tester](http://localhost:8766/tts-stt/). Expand “Testing before
Google sign-in is configured?”, enter the device key shown by `issue`, and connect.
The key stays only in that tab’s memory. Restart the server after editing `.env`.

Use the Google owner sign-in for browser settings and creating/revoking device keys.
See [setup and recovery](docs/setup.md), [Windows dictation](client/README.md), and
[Android connection](docs/android_setup.md).

## Limits that keep it small

- One speech request at a time, 5 per minute and 100 in a rolling day. Limits are
  local resource guards, not a guarantee of Google quota or a spending cap.
- Browser/Windows recordings stop at 20 seconds. Uploads must be under 1 MB;
  speech input is at most 2,000 characters. Provider timeout is 60 seconds.
- Faithful transcription; WAV/PCM speech output. No MP3 encoder, streaming,
  cleanup mode, automatic provider fallback, or invented OpenAI model aliases.
- Run one Uvicorn worker. Sessions are revoked on restart. Audit metadata expires
  after seven days when the service is used; it contains no submitted content.
- Server deployment uses the canonical private Caddy router and `/tts-stt` path.
  Do not run the obsolete per-app Tailscale Serve commands in older planning docs.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use simulated Gemini responses; no provider call or charge occurs. See
[the compatibility contract](docs/contract.md) for supported fields and limitations.
Google account setup, real speech, owner sign-in, phone acceptance and deployment
must be verified separately before calling the complete V1 project accepted.
