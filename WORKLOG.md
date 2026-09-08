# Work log — tts-stt

## 2026-09-08 — Gemini implementation checkpoint
- **Branch:** `feat/gemini-working-hub`, based on the latest multi-provider planning branch.
- **Implemented:** Mounted FastAPI audio subset; bounded fixed-origin Gemini REST adapter; encrypted SQLite credential store and verifier-only device keys; Google owner login with PKCE/state/nonce and recent-auth validation; CSRF-protected controls; browser recorder/player; F8 Windows helper; setup, recovery, Android and compatibility guides.
- **Verified:** 12 Python tests passed; `node tests/test_recorder.cjs` passed; Python compilation and JavaScript syntax passed. Running localhost page visually checked on port 8766 (8000 was occupied). One independent review found recording concurrency and recent Google auth-time issues; both corrected with regressions.
- **Pending:** No `.env`/Gemini key supplied. No real Gemini audio, Google owner login, Windows physical paste, Android acceptance, or server deployment verified. OpenRouter/generic profiles remain deferred behind live evidence. Full V1 is not complete. Authenticated state detects ciphertext edits/swaps, not host-admin database deletion/rollback; documented limit requires further hardening before full original spec acceptance.
- **Usage:** Account five-hour usage rose from 2% to 69% at final checks; finishing with a saved checkpoint to preserve allowance.

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
