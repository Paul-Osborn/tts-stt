"""Local speech-to-text on the laptop GPU. No audio leaves this machine."""
import io
import sys
import time

from fastapi import HTTPException

MODEL = 'large-v3-turbo'
# Formats the Android keyboards and the web recorder actually send.
EXTENSIONS = ('wav', 'mp3', 'm4a', 'ogg', 'flac', 'webm', 'aac')
_model = None


def load(device='cuda', compute_type='float16'):
    """Load once and keep resident; first call downloads the model."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(MODEL, device=device, compute_type=compute_type)
    return _model


async def transcribe(audio, mime='', language=''):
    import anyio
    return await anyio.to_thread.run_sync(lambda: _transcribe(audio, language))


def _transcribe(audio, language=''):
    try:
        segments, _ = load().transcribe(
            io.BytesIO(audio),
            language=language or None,
            vad_filter=True,          # drop leading/trailing silence
            condition_on_previous_text=False,  # stops runaway repetition
        )
        return ''.join(segment.text for segment in segments).strip()
    except Exception:
        # Never leak decoder internals or the audio itself into a response.
        raise HTTPException(502, 'Could not transcribe that recording. Try again.') from None


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python -m app.whisper <audio file>')
    audio = open(sys.argv[1], 'rb').read()
    start = time.perf_counter()
    load()
    loaded = time.perf_counter()
    text = _transcribe(audio)
    done = time.perf_counter()
    print(f'model load: {loaded - start:.1f}s\ntranscribe: {done - loaded:.1f}s\n\n{text}')
