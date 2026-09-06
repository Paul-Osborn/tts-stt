# Repository Rules — tts-stt

> **How to use this template:** Copy it to your new repo's root as `REPO_RULES.md`.
> Replace every `<PLACEHOLDER>`. Delete sections that don't apply. Anything not in
> angle brackets is a sane default you can keep as-is.

These rules keep the repo clean, reproducible, and safe to share. They apply to every
commit, branch, and pull request. When in doubt, favor the simplest change that keeps
the project working.

---

## 1. Scope & structure

- Describe the intended shape of the project in one or two lines, so drift is obvious:
  A Python FastAPI service under `app/` exposing OpenAI-compatible STT & TTS endpoints,
  with client helpers under `client/`, web dashboard under `app/static/`, and tests under `tests/`.
- Keep the layout predictable. Sketch the top-level structure:

  ```
  tts-stt/
  ├─ app/                    # FastAPI server, endpoints, Gemini integration, web UI
  ├─ client/                 # Windows desktop hotkey dictation client
  ├─ tests/                  # Unit and integration test suite
  ├─ requirements.txt        # Pinned Python dependencies
  ├─ README.md               # what it is + how to run it (for humans)
  ├─ AGENTS.md               # always-on rules — the single source of truth all agents follow
  ├─ CLAUDE.md               # Claude Code entry point (imports AGENTS.md)
  ├─ GEMINI.md               # Antigravity entry point (points at AGENTS.md)
  ├─ .cursor/rules/          # Cursor entry point (points at AGENTS.md)
  ├─ REPO_RULES.md           # this file — the full rationale
  ├─ PRD.md                  # project brief — what we're building and why (project-level)
  ├─ WORKLOG.md              # dated running log of what changed (project memory)
  ├─ SPEC.md                 # current feature's plan (optional, per-feature)
  ├─ lefthook.yml            # pre-commit checks (secret scan, etc.)
  ├─ .claude/                # hooks + settings that enforce these rules
  └─ .gitignore
  ```

- Don't restructure the project without updating this section first.

### One rule set, many agents

`AGENTS.md` is the single source of truth. Each agent reads a different filename, so the others
are thin pointers to it — whichever agent picks up the project reads the same rules before
touching code:

| Agent | Reads | In this repo |
|-------|-------|--------------|
| Codex | `AGENTS.md` (native) | reads it directly |
| Cursor | `AGENTS.md` (native) + `.cursor/rules/` | direct, plus an always-apply `.cursor/rules/agents.mdc` pointer |
| Claude Code | `CLAUDE.md` | `CLAUDE.md` imports `AGENTS.md` |
| Antigravity | `GEMINI.md` (+ `AGENTS.md` on v1.20.3+) | `GEMINI.md` points at `AGENTS.md` |

Edit `AGENTS.md` for any rule change; leave the pointers alone unless an agent needs a
tool-specific override.

---

## 2. What MUST NEVER be committed

Generated, machine-local, private, or large files belong in `.gitignore`, never in history:

- **Secrets** — no `.env`, API keys, tokens, or credentials in code, config, or commit
  messages. Commit a `*.example` template instead when a reference is useful.
- **Dependencies / build output** — vendored deps, `node_modules/`, `.venv/`, `build/`, `dist/`.
- **Large binaries / data** — model files, datasets, media dumps, anything re-downloadable.
- **Local state** — log files, caches, user-specific config, scratch files.
- **Editor / OS cruft** — `.vscode/`, `.idea/`, `.DS_Store`, `Thumbs.db`, `desktop.ini`.

If one slips in by accident, see §7.

### Starter `.gitignore`

Use the ready-made `gitignore.template` from this template set (copy it to `.gitignore`),
which covers secrets, dependencies, build output, local state, and editor/OS cruft. Adjust
per project. Commit it **first**, before any code, so ignored files never enter history.

---

## 3. Version control

### Setup
- Initialize once with `git init` and commit `.gitignore` **first**, before any code,
  so ignored files never enter history.
- `main` is the default branch and is always in a working state.

### Branching
- **Never commit directly to `main`.** Branch for every change.
- Branch naming: `<type>/<short-desc>` — `feat/`, `fix/`, `docs/`, `chore/`, `refactor/`.
  - `feat/add-export`, `fix/null-on-empty-input`, `docs/readme-setup`
- Delete branches after they merge.
- *(Optional but recommended)* enforce it with a hook that blocks `git commit`/`git push`
  on `main`. See `git-guard.template.ps1` in this template set.

### Commits
- One logical change per commit. Small and reviewable.
- Imperative, present-tense subject, ≤ 72 chars, no trailing period.
  - ✅ `fix: restore focus after dialog closes`   ❌ `fixed some stuff`
- Use [Conventional Commits](https://www.conventionalcommits.org) prefixes:
  `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`.
- Commit body explains **why**, not just what.
- Never commit broken code to `main`. Never `git push --force` to `main`.
- Don't rewrite published history others may have pulled.

### Pull requests
- All changes reach `main` through a PR, even solo work — it's the review checkpoint.
- Prose-only changes are review-exempt. Normal and high-risk work gets one independent final review after it is stable; record the outcome in `.claude/review/receipt.json`, fix valid findings, then open the PR.
- Once CI is green, merge the branch you have checked out with `gh pr merge --squash --delete-branch`. Never merge a PR number from another branch, merge red, or use `--admin`.
- **Authority ceiling:** A PR touching governance/rule files is the human's to merge, not yours.
- PR description states: what changed, why, and how it was tested.
- Keep PRs focused: one complete, shippable deliverable per branch, including its tests, supporting fixes, small supporting refactors, and documentation. Defer unrelated cleanup.
- A PR must build / run / pass tests (green CI) before merge.

### Plan before you code — once

- For anything beyond a one-line edit, write a short plan **before** implementing: which
  files change, what's explicitly out of scope, and how the result will be verified.
- For a real feature, copy `SPEC.template.md` to `SPEC.md` and fill it in. The spec — not the
  code — is the thing to review and agree on first. Keep it updated as decisions change.
- Reconfirm only when the approved goal, risk, or scope materially changes; routine implementation choices are the agent's to make.
- This matters most with AI agents: without an explicit plan and scope, an agent fills the
  gaps with guesses and confidently builds the wrong thing.

### Prove it works (verification)

- "Looks done" is not done. Before calling a task complete, produce evidence: test output,
  the exact command run and what it returned, or a screenshot — not just an assertion.
- Prefer a check the tool can run itself (test suite, build, linter) so mistakes are caught
  automatically instead of waiting for a human to notice them.

---

## 3a. Automatic git & guardrails (enforcement)

Git is hands-off. Whichever agent picks up the project runs the whole workflow itself — branch,
commit, push, review, open PR, and merge the checked-out branch when CI is green (`gh pr merge --squash --delete-branch`).
PRs touching governance rules require human ratification.

Written rules are only advice; an agent (or a tired human) forgets them. The rules that
actually hold are the ones a machine enforces. This kit layers guardrails so that if one is
bypassed, another still catches the problem ("defense in depth").

**Git-level guardrails (apply to EVERY agent + manual commits — via `lefthook.yml`):**
- **Branch guard** — refuses any commit made on `main`/`master`. Branch first.
- **Secret scan on commit** — Gitleaks refuses any commit containing a key, token, or
  password. This is the safety net behind §6.
- **Large-file gate** — refuses a newly added file over the configured limit (2048 KB by default).
- **Lockfile sanity check** — warns when a dependency lockfile changes without its manifest.
- Install both once with `lefthook install`.

**Claude Code-specific guardrails (via `.claude/settings.json` hooks — convenience for Claude):**
- **Git guard** — `git-guard.ps1` denies commit/push on `main`, enforces review receipts for substantive work, gates merges on green CI status, and blocks self-merging governance changes.
- **Auto-commit on turn end** — `auto-commit.ps1` (Stop hook) commits and pushes any leftover
  work so nothing is lost. Never touches `main`; the secret scan still gates its commits.
- **Protected paths** — `protect-paths.ps1` blocks edits to sensitive files/folders (including `.claude/settings.json`).
- Other agents (Codex, Cursor, Antigravity) rely on the git-level guardrails above plus the
  rules they read from `AGENTS.md`; replicate any of these in their own hook systems if wanted.

**Optional:** a CI workflow re-runs tests and the secret scan on every push, catching anything
that slipped past local checks.

Set these up at project start. Do not disable or route around a guardrail to "get unblocked" —
fix the underlying cause (branch first, remove the secret, etc.).

---

## 4. Dependencies

- Pin versions for reproducibility (`==`, lockfiles, etc.).
- Adding a dependency requires a one-line justification in the PR. Remove anything unused.
- Never hand-edit a generated dependency lockfile. Change its manifest and let the package manager regenerate the lockfile in the same commit.
- State any hard constraints here: local-first hub, API key in .env only, external network calls restricted to Google Gemini API (`generativelanguage.googleapis.com`), pinned dependencies.

---

## 5. Code hygiene

- Match the existing style and comment density. Don't reformat untouched code in a feature PR.
- No dead code, no commented-out blocks, no debug-print spam left behind.
- Preserve the project's core invariants: OpenAI API compatibility for audio endpoints (`/v1/audio/transcriptions` and `/v1/audio/speech`), asynchronous non-blocking audio handling, zero hardcoded secrets.

---

## 6. Secrets & privacy (hard line)

- No secret ever enters the repo — not in code, config, history, or a commit message.
- Before pushing, scan the diff for keys, tokens, paths with usernames, and device serials.
- State the network policy: Outbound network calls are allowed only to Google Gemini API (`generativelanguage.googleapis.com`) for audio transcription and speech synthesis. All inbound traffic is restricted to local network / Tailscale mesh.
- **Private Tailscale Serve:** Remote access is exposed strictly via `tailscale serve` over authenticated private Tailnet HTTPS addresses:
  ```bash
  tailscale serve --https=443 --set-path="/tts-stt" --bg --yes 8000
  ```
- **Tailscale URL & Naming Conventions:**
  - Full origin URL pattern: `https://<node-name>.<tailnet-name>.ts.net<route-path>` (validated by `^https://[A-Za-z0-9.-]+\.ts\.net$ROUTE_PATH$`).
  - Route path convention: Single lowercase hyphenated path (`^/[a-z0-9][a-z0-9-]*$`), default `/tts-stt`.
- **No Tailscale Funnel:** Tailscale Funnel is strictly forbidden (`allow_funnel: false`) to prevent any exposure to the public internet.
- **Origin & Host Guard:** The hub validates incoming `Host` and `Origin` headers, allowing only loopback (`127.0.0.1`, `localhost`, `::1`) and private Tailscale network origins (`*.ts.net` and `100.64.0.0/10` CGNAT range).
- If a secret is ever committed, treat it as compromised: rotate it immediately, then scrub
  history (§7). Scrubbing alone is not enough — the key is burned.

---

## 7. When something bad gets committed

- **Large file** committed by mistake: remove it, add to `.gitignore`, and if already pushed,
  purge it from history with `git filter-repo` (preferred) or BFG, then force-update the
  remote *branch* (never `main`) and have collaborators re-clone.
- **Secret** committed: rotate the secret first (assume it's leaked), then scrub history as above.

---

## 8. Governance version & updates

`.governance-version` records this repository's governance-kit generation. Before a future
upgrade, run the official updater with `-DryRun`; it replaces only unchanged, template-owned
gates and leaves the project brief, specifications, filled-in rules, secrets configuration, and
service code alone.

## 9. Releases / tags (optional)

- Tag working milestones with semantic versions: `v0.1.0`, `v0.2.0`.
- A tagged commit must satisfy passing test suite and working audio transcription/synthesis verification.

---

*These rules protect three things: a repo small enough to clone fast, a history clean of
secrets and binaries, and a project that still matches its intended shape. Change the rule
before you break it.*
