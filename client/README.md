# Windows dictation

Set up the hub first. Create a distinct device key for this PC and place it in
the local `.env` file as `HUB_CLIENT_KEY`. Set `HUB_BASE_URL` to the hub address.
For the home server this is `https://gitserver.tail97bf76.ts.net/tts-stt`.

From PowerShell in this project folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -r client/requirements.txt
.\.venv\Scripts\python.exe -m client.desktop
```

Click a text field. Hold **F8**, speak, and release. The helper records from your
default microphone for at most five minutes, transcribes, and pastes. If you switch
windows while waiting, it leaves the transcript on your clipboard instead.
Press **Ctrl+C** in the helper's terminal to stop.

The clipboard is intentionally replaced and retains the transcript; Windows
clipboard history/sync may retain it too. No recording or transcript file is
written. Test in an ordinary text editor first. Protected/admin windows and some
games may reject simulated paste. The helper does not elevate privileges.
