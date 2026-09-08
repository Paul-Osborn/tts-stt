import asyncio
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path

from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.sessions import SessionMiddleware

from . import gemini
from .config import Settings
from .store import Store

MAX_BODY = 1024 * 1024
STATIC = Path(__file__).parent / 'static'


def error(status, message):
    return JSONResponse({'error': {'message': message, 'type': 'hub_error', 'code': status}}, status_code=status)


class Speech(BaseModel):
    model_config = ConfigDict(extra='forbid')
    model: str = gemini.TTS
    input: str = Field(min_length=1, max_length=2000)
    voice: str = 'Kore'
    response_format: str = 'wav'
    speed: float = 1


def create_app(settings=None):
    settings = settings or Settings()
    store = Store(settings.state_dir, settings.root_key) if settings.root_key else None
    lock = asyncio.Lock()

    @asynccontextmanager
    async def lifespan(app):
        yield

    outer = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    hub = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    outer.state.store = store
    outer.state.settings = settings
    sessions = {}  # Opaque, revocable sessions; restart signs everyone out.
    oauth = OAuth()
    oauth.register('google', client_id=settings.google_id, client_secret=settings.google_secret,
                   authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
                   access_token_url='https://oauth2.googleapis.com/token',
                   jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
                   issuer='https://accounts.google.com',
                   client_kwargs={'scope': 'openid email', 'code_challenge_method': 'S256',
                                  'timeout': 20, 'follow_redirects': False, 'trust_env': False})

    def owner(request, recent=False):
        session = sessions.get(request.session.get('sid'))
        if not session or time.time() - session['at'] > 3600:
            raise HTTPException(401, 'Sign in with your owner Google account')
        if recent and time.time() - session['auth_at'] > 300:
            raise HTTPException(401, 'Sign in again before changing credentials')
        if request.method != 'GET' and not secrets.compare_digest(
                request.headers.get('x-csrf-token', ''), session['csrf']):
            raise HTTPException(403, 'Refresh the page before trying again')
        return session

    def authorize(request):
        header = request.headers.get('authorization', '')
        if header.startswith('Bearer ') and store and store.authenticate(header[7:]):
            return
        owner(request)

    def provider_key():
        if not store or not settings.free_tier:
            raise HTTPException(503, 'Complete setup and confirm a Gemini project with billing disabled')
        key = store.get('provider:gemini', '') or settings.gemini_key
        if not key:
            raise HTTPException(503, 'Add your Gemini key in Settings or the local .env file')
        return key

    @hub.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error(exc.status_code, exc.detail)

    @hub.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return error(400, 'Invalid request fields. See the supported audio contract.')

    @outer.middleware('http')
    async def guard(request, call_next):
        if request.headers.get('host') != settings.authority:
            return error(403, 'Untrusted host')
        if request.headers.get('origin') not in (None, settings.origin):
            return error(403, 'Untrusted origin')
        if request.method not in ('GET', 'POST', 'DELETE'):
            return error(405, 'Unsupported method')
        try:
            async with asyncio.timeout(15):
                body = bytearray()
                async for chunk in request.stream():
                    body.extend(chunk)
                    if len(body) > MAX_BODY:
                        return error(413, 'Recording too large. Use a shorter clip (under 20 seconds).')
                request._body = bytes(body)
            response = await call_next(request)
        except TimeoutError:
            return error(408, 'Upload took too long')
        except Exception:
            # Provider errors, malformed state and tracebacks never disclose request content.
            return error(503, 'Hub unavailable. Check local setup or restore the authenticated state store.')
        response.headers.update({'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
                                 'Referrer-Policy': 'no-referrer',
                                 'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"})
        return response

    @hub.get('/health')
    async def health():
        return {'status': 'ok' if store else 'setup_required', 'contract': '1.0', 'provider': 'Gemini'}

    @hub.get('/')
    async def index():
        return FileResponse(STATIC / 'index.html')

    @hub.get('/ui/{filename}')
    async def asset(filename: str):
        if filename not in ('app.js', 'style.css'):
            raise HTTPException(404, 'Not found')
        return FileResponse(STATIC / filename)

    @hub.get('/auth/login')
    async def login(request: Request):
        if not all((store, settings.google_id, settings.google_secret, settings.owner_sub, settings.owner_email)):
            raise HTTPException(503, 'Google owner sign-in is not configured. Follow the setup guide.')
        request.session.clear()
        return await oauth.google.authorize_redirect(request, settings.base_url + '/auth/callback',
                                                      prompt='select_account', max_age=0)

    @hub.get('/auth/callback')
    async def callback(request: Request):
        try:
            token = await oauth.google.authorize_access_token(request)
            user = token['userinfo']
            if (user['sub'] != settings.owner_sub or user['email'].lower() != settings.owner_email.lower()
                    or user.get('email_verified') is not True):
                raise ValueError('Not owner')
            auth_at = user.get('auth_time')
            if type(auth_at) not in (int, float) or not -30 <= time.time() - auth_at <= 300:
                raise ValueError('Google authentication is not recent')
        except Exception:
            request.session.clear()
            raise HTTPException(403, 'Google sign-in failed or this account is not the configured owner') from None
        sessions.clear()
        sid = secrets.token_urlsafe(32)
        sessions[sid] = {'at': time.time(), 'auth_at': auth_at, 'csrf': secrets.token_urlsafe(32)}
        request.session.clear()
        request.session['sid'] = sid
        return RedirectResponse(settings.base_url + '/')

    @hub.get('/control')
    async def control(request: Request):
        session = owner(request)
        return {'csrf': session['csrf'], 'ready': bool(settings.free_tier and (settings.gemini_key or store.get('provider:gemini'))),
                'devices': [{'id': ident, 'label': value['label']} for ident, value in store.devices()],
                'stt': gemini.STT, 'tts': gemini.TTS, 'voices': gemini.VOICES}

    @hub.post('/control/logout')
    async def logout(request: Request):
        owner(request)
        sessions.pop(request.session.get('sid'), None)
        request.session.clear()
        return {'ok': True}

    @hub.post('/control/devices')
    async def issue(request: Request):
        owner(request, recent=True)
        data = await request.json()
        label = data.get('label')
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 40 or len(store.devices()) >= 20:
            raise HTTPException(400, 'Use a device name of 1–40 characters; maximum 20 devices')
        ident, token = store.issue(label.strip())
        store.audit('device_issue', 200)
        return {'id': ident, 'token': token}

    @hub.delete('/control/devices/{ident}')
    async def revoke(ident: str, request: Request):
        owner(request, recent=True)
        store.delete('device:' + ident)
        store.audit('device_revoke', 200)
        return {'ok': True}

    @hub.post('/control/provider')
    async def save_provider(request: Request):
        owner(request, recent=True)
        data = await request.json()
        key = data.get('key')
        if not isinstance(key, str) or not 10 <= len(key) <= 256:
            raise HTTPException(400, 'Enter a valid Gemini API key')
        store.put('provider:gemini', key)
        store.audit('provider_replace', 200)
        return {'ok': True}

    @hub.delete('/control/provider')
    async def delete_provider(request: Request):
        owner(request, recent=True)
        store.delete('provider:gemini')
        store.audit('provider_delete', 200)
        return {'ok': True, 'env_key_present': bool(settings.gemini_key)}

    @hub.get('/v1/models')
    async def models(request: Request):
        authorize(request)
        return {'object': 'list', 'data': [{'id': model, 'object': 'model', 'created': 0,
                 'owned_by': 'google'} for model in (gemini.STT, gemini.TTS)]}

    async def run(operation, work):
        if lock.locked():
            raise HTTPException(429, 'Another recording is processing. Try again shortly.')
        async with lock:
            if not store.reserve():
                raise HTTPException(429, 'Hub limit reached (5 requests/minute, 100/day)')
            try:
                result = await work()
            except HTTPException as exc:
                store.audit(operation, exc.status_code)
                raise
            store.audit(operation, 200)
            return result

    @hub.post('/v1/audio/transcriptions')
    async def transcriptions(request: Request):
        authorize(request)
        key = provider_key()
        async with request.form(max_files=1, max_fields=4, max_part_size=MAX_BODY) as form:
            if set(form) - {'file', 'model', 'language', 'response_format'}:
                raise HTTPException(400, 'Unsupported transcription option')
            model = form.get('model', gemini.STT)
            fmt = form.get('response_format', 'json')
            language = form.get('language', '')
            if model != gemini.STT or fmt not in ('json', 'text'):
                raise HTTPException(400, 'Unsupported model or response format')
            if not isinstance(language, str) or (language and (len(language) != 2 or not language.isalpha())):
                raise HTTPException(400, 'Language must be a two-letter code')
            upload = form.get('file')
            if not hasattr(upload, 'filename'):
                raise HTTPException(400, 'An audio file is required')
            extension = (upload.filename or '').rsplit('.', 1)[-1].lower()
            mime = gemini.MIMES.get(extension)
            if not mime:
                raise HTTPException(400, 'Use WAV, MP3, M4A, OGG, FLAC, AAC or WebM audio')
            audio = await upload.read()
            if not audio:
                raise HTTPException(400, 'Recording is empty')
            text = await run('stt', lambda: gemini.transcribe(key, audio, mime, language))
        return Response(text, media_type='text/plain') if fmt == 'text' else {'text': text}

    @hub.post('/v1/audio/speech')
    async def speech(request: Request, body: Speech):
        authorize(request)
        key = provider_key()
        if (body.model != gemini.TTS or body.voice not in gemini.VOICES
                or body.response_format not in ('wav', 'pcm') or body.speed != 1 or not body.input.strip()):
            raise HTTPException(400, 'Use a listed model/voice, WAV or PCM, and speed 1')
        audio = await run('tts', lambda: gemini.speak(key, body.input, body.voice, body.response_format))
        return Response(audio, media_type='audio/wav' if body.response_format == 'wav' else 'application/octet-stream')

    hub.add_middleware(SessionMiddleware, secret_key=settings.root_key or secrets.token_hex(32),
                       session_cookie='speech_session', max_age=3600, same_site='lax',
                       https_only=settings.base_url.startswith('https:'), path='/tts-stt')
    outer.mount('/tts-stt', hub)
    return outer


app = create_app()
