import asyncio
import base64
import io
import json
import secrets
import sqlite3
import time
import wave

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import gemini
from app.config import Settings
from app.main import create_app
from app.store import Store


@pytest.fixture
def hub(tmp_path, monkeypatch):
    settings = Settings(root_key=base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
                        state_dir=tmp_path, gemini_key='test-provider-credential', free_tier=True)
    app = create_app(settings)
    ident, key = app.state.store.issue('test device')
    client = TestClient(app, base_url='http://localhost:8766')
    client.headers['Authorization'] = 'Bearer ' + key
    return client, app.state.store, ident


def test_mounted_host_auth_and_revocation(hub):
    client, store, ident = hub
    assert client.get('/tts-stt/health').json()['contract'] == '1.0'
    assert client.get('/health').status_code == 404
    assert client.get('/tts-stt/v1/models').status_code == 200
    assert client.get('/tts-stt/health', headers={'Host': 'evil.ts.net'}).status_code == 403
    assert client.post('/tts-stt/control/logout', headers={'Origin': 'https://evil.example'}).status_code == 403
    assert client.get('/tts-stt/control').status_code == 401  # device key cannot administer
    store.delete('device:' + ident)
    assert client.get('/tts-stt/v1/models').status_code == 401


def test_transcription_contract_and_cleanup(hub, monkeypatch):
    client, store, _ = hub
    async def fake(key, data, mime, language):
        assert data == b'RIFF-test' and mime == 'audio/wav' and language == 'en'
        return 'Private spoken words.'
    monkeypatch.setattr(gemini, 'transcribe', fake)
    response = client.post('/tts-stt/v1/audio/transcriptions',
                           data={'model': gemini.STT, 'language': 'en'}, files={'file': ('x.wav', b'RIFF-test')})
    assert response.json() == {'text': 'Private spoken words.'}
    assert b'Private spoken words' not in store.path.read_bytes()
    assert b'RIFF-test' not in store.path.read_bytes()
    response = client.post('/tts-stt/v1/audio/transcriptions',
                           data={'model': 'whisper-1'}, files={'file': ('x.wav', b'x')})
    assert response.status_code == 400
    assert client.post('/tts-stt/v1/audio/transcriptions', files={'file': ('x.exe', b'x')}).status_code == 400


def test_speech_and_invalid_options(hub, monkeypatch):
    client, _, _ = hub
    async def fake(key, text, voice, fmt):
        return gemini.wav_bytes(b'\x00\x00' * 100)
    monkeypatch.setattr(gemini, 'speak', fake)
    response = client.post('/tts-stt/v1/audio/speech', json={'input': 'Hello'})
    assert response.status_code == 200
    with wave.open(io.BytesIO(response.content)) as audio:
        assert (audio.getframerate(), audio.getnchannels(), audio.getsampwidth()) == (24000, 1, 2)
    for change in ({'voice': 'alloy'}, {'response_format': 'mp3'}, {'speed': 2}, {'model': 'tts-1'}, {'input': ' '}):
        assert client.post('/tts-stt/v1/audio/speech', json={'input': 'Hello', **change}).status_code == 400
    response = client.post('/tts-stt/v1/audio/speech', json={'input': {'sensitive': 'never echo'}})
    assert response.status_code == 400 and 'never echo' not in response.text


def test_upload_bound_and_headers(hub):
    client, _, _ = hub
    assert client.post('/tts-stt/v1/audio/transcriptions', content=b'a' * (1024 * 1024 + 1)).status_code == 413
    response = client.get('/tts-stt/')
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    assert 'frame-ancestors' in response.headers['content-security-policy']
    assert client.get('/tts-stt/ui/app.js').status_code == 200
    assert client.get('/tts-stt/ui/.env').status_code == 404


def test_vault_authentication_and_request_limits(hub):
    _, store, _ = hub
    store.put('provider:gemini', 'secret-value')
    assert store.get('provider:gemini') == 'secret-value'
    assert b'secret-value' not in store.path.read_bytes()
    assert [store.reserve() for _ in range(6)] == [True] * 5 + [False]
    with store.connect() as db:
        db.execute("UPDATE records SET value = ? WHERE id = 'provider:gemini'", (b'changed',))
    with pytest.raises(Exception):
        store.get('provider:gemini')


def test_setup_fails_closed(tmp_path):
    app = create_app(Settings(root_key='', state_dir=tmp_path))
    client = TestClient(app, base_url='http://localhost:8766')
    assert client.get('/tts-stt/health').json()['status'] == 'setup_required'
    assert client.get('/tts-stt/auth/login').status_code == 503
    assert client.post('/tts-stt/v1/audio/speech', json={'input': 'Hi'}).status_code == 401


@pytest.mark.parametrize('status', [302, 403, 429, 500])
def test_adapter_rejects_errors_and_redirects(monkeypatch, status):
    real_client = httpx.AsyncClient
    seen = []
    def handler(request):
        seen.append(request.url)
        assert request.url.host == 'generativelanguage.googleapis.com'
        return httpx.Response(status, headers={'Location': 'https://evil.example'}, text='provider-secret-body')
    monkeypatch.setattr(gemini.httpx, 'AsyncClient', lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(gemini.generate('key', gemini.STT, [], {}))
    assert exc.value.status_code == (429 if status == 429 else 502)
    assert 'provider-secret-body' not in exc.value.detail
    assert len(seen) == 1


def test_adapter_real_wire_contract(monkeypatch):
    real_client = httpx.AsyncClient
    def handler(request):
        data = json.loads(request.content)
        assert request.headers['x-goog-api-key'] == 'key'
        assert 'speechConfig' in data['generationConfig']
        return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'inlineData': {'mimeType': 'audio/L16;codec=pcm;rate=24000', 'data': 'AAAAAA=='}}]}}]})
    monkeypatch.setattr(gemini.httpx, 'AsyncClient', lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    assert asyncio.run(gemini.speak('key', 'Hello', 'Kore', 'wav')).startswith(b'RIFF')


def test_owner_auth_time_csrf_and_device_lifecycle(tmp_path, monkeypatch):
    from authlib.integrations.starlette_client.apps import StarletteOAuth2App
    settings = Settings(root_key=base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
                        state_dir=tmp_path, owner_sub='owner', owner_email='owner@example.com')
    claims = {'sub': 'owner', 'email': 'owner@example.com', 'email_verified': True,
              'auth_time': time.time() - 600}
    async def exchange(self, request):
        return {'userinfo': claims}
    monkeypatch.setattr(StarletteOAuth2App, 'authorize_access_token', exchange)
    client = TestClient(create_app(settings), base_url='http://localhost:8766')
    assert client.get('/tts-stt/auth/callback').status_code == 403
    claims['auth_time'] = time.time()
    assert client.get('/tts-stt/auth/callback').status_code == 200
    state = client.get('/tts-stt/control').json()
    assert client.post('/tts-stt/control/devices', json={'label': 'phone'}).status_code == 403
    client.headers['X-CSRF-Token'] = state['csrf']
    device = client.post('/tts-stt/control/devices', json={'label': 'phone'}).json()
    assert 'token' in device
    assert 'token' not in client.get('/tts-stt/control').text
    assert client.delete('/tts-stt/control/devices/' + device['id']).status_code == 200
    assert client.post('/tts-stt/control/logout').status_code == 200
    assert client.get('/tts-stt/control').status_code == 401
