"""Hold F8 to dictate; keeps audio in memory and never saves transcripts."""
import ctypes
import io
import os
import time
import wave

import httpx
from dotenv import load_dotenv

from app.config import ROOT, Settings


def main():
    if os.name != 'nt':
        raise SystemExit('This helper runs on Windows.')
    import pyperclip
    import sounddevice as sd

    load_dotenv(ROOT / '.env')
    settings = Settings()
    key = os.getenv('HUB_CLIENT_KEY', '')
    if not key:
        raise SystemExit('Add this PC’s device key as HUB_CLIENT_KEY in the local .env file.')
    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = ctypes.c_void_p
    pressed = lambda: bool(user32.GetAsyncKeyState(0x77) & 0x8000)  # F8
    print('Hold F8 to speak (5 minutes maximum). Release to paste. Ctrl+C quits.')
    try:
        while True:
            if not pressed():
                time.sleep(0.04)
                continue
            target = user32.GetForegroundWindow()
            pcm = bytearray()
            try:
                with sd.RawInputStream(samplerate=16000, channels=1, dtype='int16') as mic:
                    while pressed() and len(pcm) < 9_600_000:  # 5 minutes at 16 kHz mono
                        data, overflow = mic.read(1600)
                        if overflow:
                            raise RuntimeError('Microphone could not keep up. Try again.')
                        pcm.extend(data)
                if len(pcm) < 6400:
                    continue
                output = io.BytesIO()
                with wave.open(output, 'wb') as audio:
                    audio.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                    audio.writeframes(pcm)
                with httpx.Client(timeout=75, follow_redirects=False, trust_env=False) as client:
                    response = client.post(settings.base_url + '/v1/audio/transcriptions',
                        headers={'Authorization': 'Bearer ' + key},
                        files={'file': ('dictation.wav', output.getvalue(), 'audio/wav')})
                if response.status_code != 200:
                    print('Dictation failed. Check that the hub is running, then retry.')
                    continue
                text = response.json()['text']
                if text:
                    pyperclip.copy(text)
                    if target == user32.GetForegroundWindow():
                        for code in (0x11, 0x56):
                            user32.keybd_event(code, 0, 0, 0)
                        for code in (0x56, 0x11):
                            user32.keybd_event(code, 0, 2, 0)
                        print('Pasted; transcript also remains on your clipboard.')
                    else:
                        print('Window changed. Transcript is on your clipboard; paste it where you want.')
            except (httpx.HTTPError, ValueError, KeyError, RuntimeError, sd.PortAudioError):
                print('Could not record or transcribe. Check the microphone and web tester, then retry.')
            finally:
                while pressed():
                    time.sleep(0.05)
    except KeyboardInterrupt:
        print('\nStopped.')


if __name__ == '__main__':
    main()
