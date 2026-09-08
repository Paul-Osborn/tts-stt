# Owner setup, private deployment and recovery

## Google sign-in

Create a Google OAuth web client for this private application. Set its redirect URI
to the **exact** `HUB_BASE_URL` plus `/auth/callback`. Local development uses
`http://localhost:8766/tts-stt/auth/callback`. Production uses
`https://gitserver.tail97bf76.ts.net/tts-stt/auth/callback`.

Put its client ID/secret in `.env`, plus the owner's verified Google subject ID
(`GOOGLE_OWNER_SUB`) and email (`GOOGLE_OWNER_EMAIL`). Obtain the subject from a
verified Google identity response during account setup; never guess it or accept
an unverified token. Missing values keep sign-in disabled. Authlib verifies the
signature, issuer, audience, expiry, state and nonce; login also uses PKCE.
Access tokens are not retained. One owner session lasts one hour; sensitive
credential actions require sign-in within five minutes. Restart logs everyone out.

The tester can use a locally issued device credential while Google setup is
pending. That credential cannot reach browser administration.

## Secrets and recovery

`HUB_ROOT_KEY` is random, created locally, and stays in `.env`. AES-256-GCM binds
each encrypted state record to its identifier. Device keys are stored only as
SHA-256 verifiers inside encrypted records. Local SQLite transactions make updates
atomic; altered ciphertext or swapped records fail closed. Deletion/rollback of
an entire database by someone with OS access is not detectable by this store.
Protect the host and do not treat encryption as protection against its administrator.

Protect `.env` and `.state` using the service account's filesystem permissions;
POSIX mode is restricted automatically. Windows permissions must be checked at
deployment: Python chmod does not replace Windows ACLs. Exclude both paths from
cloud synchronization, ordinary backups, crash uploads and source control. Do not
enable access/body logging or memory crash dumps on the service or reverse proxy.
Store the recovery password separately from the computer. It is scrypt-hashed in
`.env`. A lost root means encrypted credentials are unrecoverable.

Local emergency commands (on the hub computer, prompted for recovery password):

```powershell
.\.venv\Scripts\python.exe -m app.manage list
.\.venv\Scripts\python.exe -m app.manage revoke DEVICE_ID
.\.venv\Scripts\python.exe -m app.manage issue "Replacement phone"
```

If Google sign-in is unavailable, these commands recover device access. Repair
the owner allowlist/OAuth configuration locally and restart; the browser has no
password bypass.

Root rotation/loss uses deliberate re-enrollment, avoiding a fragile migration:
stop the service; revoke old device credentials; remove the old `.state` and
root/recovery entries locally; run `init`; issue replacement device keys; restart
and verify. This invalidates every old device and session. Keep the service stopped
throughout. Never restore old state after revocation. No plaintext secret export or
state backup is supported.

## Minisforum deployment (pending live verification)

Use a dedicated unprivileged account, private checkout/venv and `.env`, one worker,
loopback binding, no access log, restart on failure and `LimitCORE=0`. The server
command is `python -m uvicorn app.main:app --host 127.0.0.1 --port 8766 --no-access-log`.
Set `HUB_BASE_URL=https://gitserver.tail97bf76.ts.net/tts-stt`.

Before routing changes run the governance kit's `Validate-ServerRouter.ps1`.
Add `/tts-stt` to the canonical routes manifest, preserving the full prefix;
deploy Caddy and portal together through the canonical tooling, then verify
existing occupants and mounted audio endpoints. Do not alter Tailscale Serve's
single root proxy. Do not open LAN/public ports or use Funnel. Deployment has not
been performed by this implementation checkpoint.

Acceptance: verify real Google sign-in, rejected non-owner sign-in, revocation,
one spoken transcription, audible TTS, actual Free Tier account limits, phone
insertion, Windows insertion, and cleanup after interrupted uploads/provider
failure. Record results before marking a provider profile accepted.
