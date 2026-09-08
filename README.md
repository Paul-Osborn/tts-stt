# Speech Hub

A small private speech hub: dictate from your phone, the browser, or Windows, and
get the words back as text. Your recordings are transcribed by a Whisper model
running on this computer's graphics card. Nothing is sent anywhere, and no
recording or transcript is saved.

## Start on this Windows PC

Open PowerShell in this project folder. Run each command separately:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.manage init
```

The setup command asks for a recovery password and creates the private `.env`
settings file. The first time the server starts it downloads the speech model
(about 1.5 GB) and then keeps it in the graphics card's memory, so start-up takes
a few seconds and every dictation after that is fast.

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

- One recording is transcribed at a time; a second request while one is running is
  turned away rather than queued. The graphics card has room for one model.
- Recordings must be under 25 MB — roughly ten minutes of ordinary speech. The
  Windows hotkey stops recording after five minutes.
- Faithful transcription only. No cleanup mode, no text-to-speech, no invented
  OpenAI model aliases. The `model` field clients send is ignored; there is one
  engine.
- Needs an NVIDIA graphics card with CUDA. This runs on the laptop, not the
  always-on mini PC, so dictation is unavailable while the laptop is asleep.
- Run one Uvicorn worker. Sessions are revoked on restart. Audit metadata expires
  after seven days when the service is used; it contains no submitted content.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

The tests use a stand-in for the speech engine, so they run without a graphics
card. To check the real engine on an audio file:

```powershell
.\.venv\Scripts\python.exe -m app.whisper "C:\path\to\recording.wav"
```

See [the compatibility contract](docs/contract.md) for supported fields and
limitations. Real phone dictation and the Windows paste still need verifying on
the actual devices.
