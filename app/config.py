import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')


@dataclass
class Settings:
    base_url: str = os.getenv('HUB_BASE_URL', 'http://localhost:8766/tts-stt')
    root_key: str = os.getenv('HUB_ROOT_KEY', '')
    google_id: str = os.getenv('GOOGLE_CLIENT_ID', '')
    google_secret: str = os.getenv('GOOGLE_CLIENT_SECRET', '')
    owner_sub: str = os.getenv('GOOGLE_OWNER_SUB', '')
    owner_email: str = os.getenv('GOOGLE_OWNER_EMAIL', '')
    state_dir: Path = ROOT / '.state'

    def __post_init__(self):
        url = urlsplit(self.base_url)
        if (url.path != '/tts-stt' or url.query or url.fragment or url.username
                or url.password or url.scheme not in ('http', 'https')):
            raise ValueError('HUB_BASE_URL must be a fixed private URL ending in /tts-stt')
        if url.hostname not in ('localhost', '127.0.0.1', '::1'):
            # Any machine on the owner's own Tailscale network, so the hub can run on the
            # laptop that holds the GPU as well as the mini PC. Nothing public resolves here.
            if url.scheme != 'https' or not url.hostname.endswith('.tail97bf76.ts.net'):
                raise ValueError('Remote URL must use a machine on the private Tailscale network')

    @property
    def origin(self):
        url = urlsplit(self.base_url)
        return f'{url.scheme}://{url.netloc}'

    @property
    def authority(self):
        return urlsplit(self.base_url).netloc
