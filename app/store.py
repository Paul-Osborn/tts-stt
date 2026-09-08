"""Small authenticated store: secrets encrypted, device keys hashed, no content."""
import base64
import hashlib
import json
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class Store:
    def __init__(self, directory, root_key):
        key = base64.urlsafe_b64decode(root_key)
        if len(key) != 32:
            raise ValueError('HUB_ROOT_KEY must encode 32 random bytes')
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.path = directory / 'hub.sqlite3'
        self.cipher = AESGCM(key)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, value BLOB NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS audit (at INTEGER, operation TEXT, status INTEGER)')
        os.chmod(self.path, 0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    def encode(self, name, value):
        nonce = secrets.token_bytes(12)
        return nonce + self.cipher.encrypt(nonce, json.dumps(value).encode(), name.encode())

    def decode(self, name, value):
        return json.loads(self.cipher.decrypt(value[:12], value[12:], name.encode()))

    def put(self, name, value):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO records VALUES (?, ?)', (name, self.encode(name, value)))

    def get(self, name, default=None):
        with self.connect() as db:
            row = db.execute('SELECT value FROM records WHERE id = ?', (name,)).fetchone()
        return self.decode(name, row[0]) if row else default

    def issue(self, label):
        token = secrets.token_urlsafe(32)
        ident = secrets.token_hex(8)
        self.put('device:' + ident, {'label': label, 'hash': hashlib.sha256(token.encode()).hexdigest()})
        return ident, token

    def devices(self):
        with self.connect() as db:
            rows = db.execute("SELECT id, value FROM records WHERE id LIKE 'device:%'").fetchall()
        return [(name[7:], self.decode(name, value)) for name, value in rows]

    def authenticate(self, token):
        digest = hashlib.sha256(token.encode()).hexdigest()
        return any(secrets.compare_digest(value['hash'], digest) for _, value in self.devices())

    def delete(self, name):
        with self.connect() as db:
            db.execute('DELETE FROM records WHERE id = ?', (name,))

    def audit(self, operation, status):
        with self.connect() as db:
            db.execute('DELETE FROM audit WHERE at < ?', (int(time.time()) - 7 * 86400,))
            db.execute('INSERT INTO audit VALUES (?, ?, ?)', (int(time.time()), operation, status))
