# tts-stt — Claude Code entry point

> **How to use this template:** Copy it to your new repo's root as `CLAUDE.md`. Claude Code
> reads this file automatically every session. To avoid keeping two copies of the rules, this
> file just **points at `AGENTS.md`** (the rules every agent reads) and adds the few things
> specific to Claude Code. Edit `AGENTS.md` for the actual rules.

The project rules live in `AGENTS.md`. Read it now and treat it as standing instructions:

@AGENTS.md

## Claude-specific notes

- **Git is hands-off and pre-authorized.** `.claude/settings.json` allowlists the `git` and
  `gh pr` commands, so you are never prompted. Run the full workflow from `AGENTS.md` yourself
  (branch → commit → push → review → open PR → merge green PR) and merge when green via `gh pr merge`.
- **Guardrails are wired here.** `.claude/settings.json` activates the hooks that enforce the
  rules:
  - `.claude/hooks/git-guard.ps1` — enforces branch guard, review receipt, green CI merge gate, and authority ceiling.
  - `.claude/hooks/protect-paths.ps1` — denies edits to protected files.
  - `.claude/hooks/auto-commit.ps1` — Stop hook; auto-saves leftover work at end of turn.
  Don't try to work around a blocked action — fix the cause (branch first, remove the secret).
- **Plan mode for non-trivial work.** Explore and plan before switching to implementation,
  per "plan before you code" in `AGENTS.md`.
- **Keep this file short.** Real rules go in `AGENTS.md` so every agent sees them, not just
  Claude.
