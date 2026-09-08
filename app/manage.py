"""Local setup/recovery. Run on the hub computer, never through a web endpoint."""
import argparse
import base64
import getpass
import hashlib
import os
import secrets

from dotenv import dotenv_values, set_key

from .config import ROOT, Settings
from .store import Store


def main():
    parser = argparse.ArgumentParser(description='Speech Hub local setup and recovery')
    parser.add_argument('action', choices=('init', 'issue', 'list', 'revoke'))
    parser.add_argument('value', nargs='?', help='device label or device ID')
    args = parser.parse_args()
    path = ROOT / '.env'
    if args.action == 'init':
        values = dotenv_values(path)
        if values.get('HUB_ROOT_KEY'):
            parser.error('Already initialized; existing secrets were not changed')
        password = getpass.getpass('Choose a local recovery password (at least 16 characters): ')
        if len(password) < 16 or password != getpass.getpass('Repeat recovery password: '):
            parser.error('Passwords must match and have at least 16 characters')
        if not path.exists():
            path.write_text((ROOT / '.env.example').read_text(), encoding='utf-8')
        salt = secrets.token_bytes(16)
        verifier = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1).hex()
        set_key(path, 'HUB_ROOT_KEY', base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())
        set_key(path, 'RECOVERY_VERIFIER', salt.hex() + ':' + verifier)
        os.chmod(path, 0o600)
        print('Initialized. Keep .env private. Now add your Gemini key and confirm Free Tier.')
        return
    values = dotenv_values(path)
    try:
        salt, expected = values['RECOVERY_VERIFIER'].split(':')
        password = getpass.getpass('Local recovery password: ')
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
        if not secrets.compare_digest(actual, expected):
            parser.error('Incorrect recovery password')
    except (KeyError, ValueError, AttributeError):
        parser.error('Run init first')
    store = Store(Settings().state_dir, values['HUB_ROOT_KEY'])
    if args.action == 'issue':
        if not args.value or not 1 <= len(args.value) <= 40 or len(store.devices()) >= 20:
            parser.error('Supply a name of 1–40 characters; maximum 20 devices')
        ident, token = store.issue(args.value)
        print(f'Device ID: {ident}\nDevice key (shown once): {token}')
    elif args.action == 'list':
        for ident, value in store.devices():
            print(ident, value['label'])
    elif args.action == 'revoke':
        if not args.value:
            parser.error('Supply the device ID from list')
        store.delete('device:' + args.value)
        print('Revoked.')


if __name__ == '__main__':
    main()
