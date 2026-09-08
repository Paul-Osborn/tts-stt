# Work log — tts-stt

## 2026-09-08 — Punctuation proven, and the phone can now reach the hub
- **Branch:** `fix/laptop-tailscale-address`
- **Punctuation settled:** the owner recorded a real sentence through the browser tester on the
  GPU and the transcript came back punctuated. The synthetic-voice caveat from the earlier entry
  is closed; nothing about punctuation is outstanding.
- **Changed:** `app/config.py` accepted a base address only on localhost or
  `gitserver.tail97bf76.ts.net`, so the phone had no address it was allowed to use now that the
  model runs on the laptop. It now accepts any `*.tail97bf76.ts.net` host over HTTPS — the
  owner's own Tailscale network, nothing public — with a test covering the accepted and rejected
  forms. `docs/android_setup.md` now points at `leeloo.tail97bf76.ts.net` and carries the one
  `tailscale serve` command that publishes the loopback hub on it.
- **Still unproven:** the Android keyboard itself. No APK has been tested.
- **Gotcha:** `tailscale serve --set-path=/tts-stt` strips the prefix before forwarding, so the
  mounted hub sees `/` and returns `{"detail":"Not Found"}`. Proxy the root instead:
  `tailscale serve --bg --https=443 8766`. Same single-root-proxy shape as the mini PC.
- **Verified on the phone:** the hub page loads at `https://leeloo.tail97bf76.ts.net/tts-stt/`
  over Tailscale.

## 2026-09-08 — Local engine wired in; the cloud provider is gone
- **Branch:** `feat/local-whisper`
- **Changed:** `/v1/audio/transcriptions` now runs the local Whisper engine. Deleted
  `app/gemini.py`, `POST /v1/audio/speech` and its half of the tester, the encrypted provider
  vault, the free-tier gate and the request quota. Rewrote `PRD.md`, `REPO_RULES.md`, `AGENTS.md`
  and `SPEC.md`, which still forbade local models and capped the server at 200 MB of RAM.
  Retired `docs/implementation.md`.
- **Limits changed on purpose:** the 1 MB body cap and the 5/minute quota existed to protect a
  free tier that no longer exists, and they were also a second thing cutting the owner off.
  Uploads now cap at 25 MB (~10 minutes of speech) and the F8 hotkey records for up to 5 minutes.
  The `model` field is accepted and ignored so keyboards that hardcode `whisper-1` just work.
- **Verified:** real end-to-end run through the mounted endpoint on the GPU — startup model load
  6.2s, first request 2.1s, steady state **0.7s**, correct transcript, and the audio bytes are
  provably absent from the state database. 6 Python tests and the recorder regression pass without
  a GPU (stand-in engine).
- **Still unproven:** punctuation on a real human voice (the test clip is the Windows synthetic
  voice, which has no prosody to punctuate from — its transcript comes back unpunctuated, exactly
  as predicted); Android keyboard dictation; the Windows physical paste.
- **Next:** record one real sentence to settle punctuation, then set up the phone keyboard.
- **Blocker found for phone use (2026-09-08, not yet fixed):** `app/config.py` only accepts a
  base address on localhost or `gitserver.tail97bf76.ts.net`. The model now runs on the laptop,
  whose Tailscale name is `leeloo.tail97bf76.ts.net`, so the phone has no address it is allowed
  to use. The fix is to allow the laptop's own Tailscale hostname in `Settings.__post_init__`
  and serve it with `tailscale serve` on the laptop pointing at loopback `127.0.0.1:8766`
  (keeps the loopback binding rule). `docs/android_setup.md` still names the mini PC address and
  needs the same correction. Not done here because PR #4 is already open and reviewed.

## 2026-09-08 — Local GPU transcription proven on the laptop
- **Branch:** `feat/local-whisper`
- **Direction change:** the owner replaced the cloud provider with local models, speech-to-text
  only, text-to-speech dropped. Reasoning and the constraints it invalidates are in
  `docs/local-stt-direction.md`. Compute runs on the laptop RTX 3060, not the mini PC; the
  owner has accepted that dictation is unavailable when the laptop is asleep.
- **Changed:** Added `app/whisper.py`, a local Whisper large-v3-turbo adapter, and pinned the
  CUDA runtime wheels. Nothing is wired into the endpoint yet.
- **Verified:** Real transcription on the GPU. Model load 4.8s once at startup, then **0.7s**
  steady state for a 20-second clip (first call after load 1.9s while kernels warm). Transcript
  was complete and verbatim with no truncation.
- **Caveat on punctuation:** the test clip was generated with the Windows synthetic voice, which
  has no natural prosody, so mid-sentence punctuation could not be judged from it. Whisper
  punctuates from phrasing and pauses. **This still needs one real recording of the owner
  speaking before the punctuation claim is proven.**
- **Fixed along the way:** CTranslate2 resolves `cublas64_12.dll` through `PATH`, which does not
  include the site-packages location pip installs it to on Windows. `os.add_dll_directory` does
  not help; `app/whisper.py` prepends the paths to `PATH` before loading.
- **Next:** point `/v1/audio/transcriptions` at the local engine; remove the Gemini adapter,
  `/v1/audio/speech`, the provider vault, free-tier gate and quota limits; update the tests
  (they still assert the Gemini and speech behaviour); rewrite the 200 MB / no-local-models
  constraints in `PRD.md` and `REPO_RULES.md`; then set up the phone keyboard.

## 2026-09-08 — Gemini implementation checkpoint
- **Branch:** `feat/gemini-working-hub`, based on the latest multi-provider planning branch.
- **Implemented:** Mounted FastAPI audio subset; bounded fixed-origin Gemini REST adapter; encrypted SQLite credential store and verifier-only device keys; Google owner login with PKCE/state/nonce and recent-auth validation; CSRF-protected controls; browser recorder/player; F8 Windows helper; setup, recovery, Android and compatibility guides.
- **Verified:** 12 Python tests passed; `node tests/test_recorder.cjs` passed; Python compilation and JavaScript syntax passed. Running localhost page visually checked on port 8766 (8000 was occupied). One independent review found recording concurrency and recent Google auth-time issues; both corrected with regressions.
- **Pending:** No `.env`/Gemini key supplied. No real Gemini audio, Google owner login, Windows physical paste, Android acceptance, or server deployment verified. OpenRouter/generic profiles remain deferred behind live evidence. Full V1 is not complete. Authenticated state detects ciphertext edits/swaps, not host-admin database deletion/rollback; documented limit requires further hardening before full original spec acceptance.
- **Usage:** Account five-hour usage rose from 2% to 69% at final checks; finishing with a saved checkpoint to preserve allowance.
- **Published:** Implementation `e88f7ec` pushed to Forgejo and GitHub. [PR #3](https://gitserver.tail97bf76.ts.net/git/paul/tts-stt/pulls/3) targets the planning branch; merge/acceptance remains pending. Local preview server stopped after verification.

> **How to use this template:** Copy to `WORKLOG.md`. Append a dated entry whenever you finish
> or meaningfully advance a task. Newest at the top. This is the project's memory between
> sessions — if a decision isn't written here, the next session won't know it. Keep entries
> short; link to PRs/specs instead of re-explaining.

## 2026-09-06 — Finalize multi-provider Version 1 planning
- **Branch:** `docs/multprovider-v1-spec`
- **Changed:** Replaced the Gemini-only plan with the approved staged multi-provider V1 specification and aligned the brief/rules with the encrypted provider-vault and per-client credential architecture; no application, provider, OAuth, routing, or deployment work was authorized.
- **Verified by:** Approved Red–Blue–Red specification reviews and official pricing/provider research, then targeted document consistency checks.
- **Next:** Owner review and human merge of this governance/documentation PR; implementation remains unapproved.
- **Open decisions:** Setup-time provider capability, Free Tier availability, owner Google identity, recovery configuration, and real-device evidence must be verified during implementation.

### Handoff checkpoint
- Planning document commit: `7d1ecce` on `docs/multprovider-v1-spec`.
- Targeted consistency checks and pre-commit gates passed. The required governance review could not run because the reviewer hit its usage limit; no PR was opened and no implementation is authorized.
- Next agent: push/check both remotes if needed, obtain one independent final review and receipt, then open the owner-merge-only PR against `feat/stt-tts-hub-server`. Do not deploy, configure providers/OAuth, or alter shared routing.

## 2026-09-06 — Upgrade repository governance to V2
- **Branch:** `chore/governance-v2`
- **Changed:** Applied the official V2 gate update and aligned generic governance guidance; kept the Gemini, OpenAI-compatible audio API, private `/tts-stt` Tailscale mount, no-Funnel, and host/origin-guard requirements unchanged.
- **Verified by:** Official updater preview after application and targeted governance acceptance checks.
- **Next:** Create the `paul/tts-stt` Forgejo repository, then push this reviewed branch and open the owner-merge-only governance PR.
- **Open decisions:** Forgejo currently refuses repository creation by push.

## 2026-09-04 — Configure git remote for self-hosted Forgejo gitserver
- **Branch:** `feat/stt-tts-hub-server`
- **Changed:** Configured origin remote to `ssh://git@gitserver.tail97bf76.ts.net:22/paul/tts-stt.git` for self-hosted Forgejo server mirroring.
- **Verified by:** SSH connection to `git@gitserver.tail97bf76.ts.net` verified successful (authenticated key `leeloo-laptop`).
- **Next:** Push initial branches (`main` and `feat/stt-tts-hub-server`) once empty repo is created on Forgejo.
- **Open decisions:** None.

## 2026-09-04 — Align repository rules and spec with Tailscale server conventions
- **Branch:** `feat/stt-tts-hub-server`
- **Changed:** Incorporated server naming and Tailscale conventions into `REPO_RULES.md`, `SPEC.md`, and `PRD.md`: private Tailscale Serve routing (`tailscale serve --https=443 --set-path="/tts-stt"`), origin regex (`https://<node>.<tailnet>.ts.net/tts-stt`), origin/host guard middleware requirement (`app/origin_guard.py`), and explicit prohibition of Tailscale Funnel.
- **Verified by:** Git diff and schema verification against established workspace server rules (`pauls-software-factory`).
- **Next:** Await user approval of updated implementation plan, then proceed with implementation.
- **Open decisions:** None.

## 2026-09-04 — Initialize repository governance & PRD
- **Branch:** `chore/repo-governance`
- **Changed:** Scaffolding project governance via `new-governed-repo.ps1`, authored `PRD.md` capturing project scope (FastAPI hub for STT/TTS using Gemini models on Minisforum, Whisper IME on Android, hotkey client on Windows), filled all placeholders in `AGENTS.md` and `REPO_RULES.md`.
- **Verified by:** Git branch check, placeholder search via PowerShell regex, and rule compliance verification.
- **Next:** User review and approval of the plan, followed by implementation of the core FastAPI hub endpoints.
- **Open decisions:** None.
