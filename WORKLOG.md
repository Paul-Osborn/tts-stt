# Work log — tts-stt

> **How to use this template:** Copy to `WORKLOG.md`. Append a dated entry whenever you finish
> or meaningfully advance a task. Newest at the top. This is the project's memory between
> sessions — if a decision isn't written here, the next session won't know it. Keep entries
> short; link to PRs/specs instead of re-explaining.

## 2026-09-06 — Upgrade repository governance to V2
- **Branch:** `chore/governance-v2`
- **Changed:** Applied the official V2 gate update and aligned generic governance guidance; kept the Gemini, OpenAI-compatible audio API, private `/tts-stt` Tailscale mount, no-Funnel, and host/origin-guard requirements unchanged.
- **Verified by:** Official updater preview after application and targeted governance acceptance checks.
- **Next:** Independent governance review and owner merge of the governance PR.
- **Open decisions:** None.

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
