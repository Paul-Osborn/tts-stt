import base64
import secrets
import time

import pytest
from fastapi.testclient import TestClient

from app import main, whisper
from app.config import Settings
from app.main import create_app


@pytest.fixture
def hub(tmp_path):
    settings = Settings(root_key=base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
                        state_dir=tmp_path)
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
    async def fake(data, language):
        assert data == b'RIFF-test' and language == 'en'
        return 'Private spoken words.'
    monkeypatch.setattr(whisper, 'transcribe', fake)
    response = client.post('/tts-stt/v1/audio/transcriptions',
                           data={'model': 'whisper-1', 'language': 'en'}, files={'file': ('x.wav', b'RIFF-test')})
    assert response.json() == {'text': 'Private spoken words.'}
    assert b'Private spoken words' not in store.path.read_bytes()
    assert b'RIFF-test' not in store.path.read_bytes()
    response = client.post('/tts-stt/v1/audio/transcriptions',
                           data={'response_format': 'srt'}, files={'file': ('x.wav', b'x')})
    assert response.status_code == 400
    assert client.post('/tts-stt/v1/audio/transcriptions', files={'file': ('x.exe', b'x')}).status_code == 400


def test_upload_bound_and_headers(hub, monkeypatch):
    client, _, _ = hub
    monkeypatch.setattr(main, 'MAX_BODY', 1024)
    assert client.post('/tts-stt/v1/audio/transcriptions', content=b'a' * 1025).status_code == 413
    response = client.get('/tts-stt/')
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    assert 'frame-ancestors' in response.headers['content-security-policy']
    assert client.get('/tts-stt/ui/app.js').status_code == 200
    assert client.get('/tts-stt/ui/.env').status_code == 404


def test_store_is_authenticated(hub):
    _, store, _ = hub
    store.put('note', 'secret-value')
    assert store.get('note') == 'secret-value'
    assert b'secret-value' not in store.path.read_bytes()
    with store.connect() as db:
        db.execute("UPDATE records SET value = ? WHERE id = 'note'", (b'changed',))
    with pytest.raises(Exception):
        store.get('note')


def test_setup_fails_closed(tmp_path):
    app = create_app(Settings(root_key='', state_dir=tmp_path))
    client = TestClient(app, base_url='http://localhost:8766')
    assert client.get('/tts-stt/health').json()['status'] == 'setup_required'
    assert client.get('/tts-stt/auth/login').status_code == 503
    assert client.post('/tts-stt/v1/audio/transcriptions',
                       files={'file': ('x.wav', b'x')}).status_code == 401


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
    assert state['stt'] == whisper.MODEL
    assert client.post('/tts-stt/control/devices', json={'label': 'phone'}).status_code == 403
    client.headers['X-CSRF-Token'] = state['csrf']
    device = client.post('/tts-stt/control/devices', json={'label': 'phone'}).json()
    assert 'token' in device
    assert 'token' not in client.get('/tts-stt/control').text
    assert client.delete('/tts-stt/control/devices/' + device['id']).status_code == 200
    assert client.post('/tts-stt/control/logout').status_code == 200
    assert client.get('/tts-stt/control').status_code == 401

def test_base_url_allows_only_the_private_network():
    for good in ('http://localhost:8766/tts-stt', 'https://leeloo.tail97bf76.ts.net/tts-stt',
                 'https://gitserver.tail97bf76.ts.net/tts-stt'):
        assert Settings(base_url=good).authority
    for bad in ('http://leeloo.tail97bf76.ts.net/tts-stt',      # must be https off-machine
                'https://evil.example/tts-stt',
                'https://tail97bf76.ts.net.evil.example/tts-stt',
                'https://leeloo.tail97bf76.ts.net/other'):
        with pytest.raises(ValueError):
            Settings(base_url=bad)
