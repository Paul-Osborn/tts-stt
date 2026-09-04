# PreToolUse hook (Bash): every git/gh policy for this repo, in one place.
#
# INSTALL: copy to `.claude/hooks/git-guard.ps1`. REPLACES block-main-git.ps1 --
# delete that file after installing this one, and update .claude/settings.json to
# point at this script.
#
# WHY ONE FILE: Claude Code runs every matching PreToolUse hook on every Bash call.
# Five separate guards would mean five PowerShell process spawns per command, which
# is genuinely slow on Windows. One script, clearly sectioned, costs one spawn.
#
# The five rules, in order:
#   1. No-verify guard   -- refuses --no-verify / `git commit -n` (one-flag lefthook bypass)
#   2. Branch guard      -- refuses commit/push on main/master (was block-main-git.ps1)
#   3. Review receipt    -- refuses `gh pr create` unless the diff was reviewed
#   4. Merge gate        -- refuses `gh pr merge` when checks aren't green, or --admin is used
#   5. Authority ceiling -- refuses `gh pr merge` when the PR edits the rules themselves
#
# FAIL DIRECTION: rules 1-3 fail OPEN (a parse or git error gets out of the way).
# Rule 4/5 fail CLOSED -- if check status can't be determined, the merge is refused.
# Merging is the irreversible one; "I couldn't tell" must not mean "go ahead".

$ErrorActionPreference = 'Stop'

function Deny([string]$reason) {
    $out = @{
        hookSpecificOutput = @{
            hookEventName            = 'PreToolUse'
            permissionDecision       = 'deny'
            permissionDecisionReason = $reason
        }
    } | ConvertTo-Json -Compress -Depth 5
    Write-Output $out
    exit 0
}

try {
    $raw = [Console]::In.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
    $payload = $raw | ConvertFrom-Json
} catch {
    exit 0  # can't parse -- stay out of the way
}

$cmd = [string]$payload.tool_input.command
if ([string]::IsNullOrWhiteSpace($cmd)) { exit 0 }

# Blank out quoted strings before pattern matching, so a commit MESSAGE that happens
# to mention "--no-verify" or "gh pr merge" doesn't trip a guard. Matching runs on
# $cmdClean; anything shown back to the user uses the original $cmd.
$cmdClean = $cmd -replace '"[^"]*"', '""' -replace "'[^']*'", "''"

# ---------------------------------------------------------------------------
# 0. Shell Redirection Guard
# ---------------------------------------------------------------------------
# Prevents shell redirection (`>` or `>>`) from bypassing protect-paths.ps1 by overwriting
# protected governance files (.claude/settings.json, hooks, workflows, rules).
if ($cmdClean -match '>>?\s*(\.claude/|\.github/|AGENTS\.md|REPO_RULES\.md|CLAUDE\.md|GEMINI\.md|lefthook\.yml|\.gitleaks\.toml)') {
    Deny @"
Refused: shell redirection ('>' or '>>') targeting protected governance paths is blocked.

Edits to rules, hooks, CI workflows, and settings must be made deliberately, not via shell redirection.
"@
}

# ---------------------------------------------------------------------------
# 1. No-verify guard
# ---------------------------------------------------------------------------
# `git commit --no-verify` skips lefthook entirely -- branch guard and secret scan
# both. It is a one-flag hole through the whole local gate.
# `-n` is only dangerous on commit (on push it means --dry-run, which is harmless).
# Detects standalone `--no-verify`, `-n`, and bundled short flags (e.g. `-anm`).
if ($cmdClean -match '\bgit\b[^&|;]*--no-verify\b' -or
    $cmdClean -match '\bgit\s+commit\b[^&|;]*\s-[a-zA-Z0-9]*n[a-zA-Z0-9]*\b') {
    Deny @"
Refused: --no-verify skips the pre-commit checks (branch guard + secret scan).

AGENTS.md: don't disable or work around a guardrail to get unblocked -- fix the
underlying cause instead. If a hook is failing, read what it said and address it.
If the hook itself is wrong, that's a governance change: raise it with Paul.
"@
}

# ---------------------------------------------------------------------------
# 2. Branch guard  (preserved from block-main-git.ps1)
# ---------------------------------------------------------------------------
# Match primary subcommands per segment so `git log --grep=commit` and `git stash push` are allowed.
$isCommitOrPush = $false
foreach ($segment in ($cmdClean -split '[&|;]')) {
    if ($segment -match '^\s*git\s+(?:-[Cc]\s+\S+\s+)*(commit|push)\b' -and
        $segment -notmatch '\bgit\s+stash\s+push\b') {
        $isCommitOrPush = $true
        break
    }
}

if ($isCommitOrPush) {

    # Prefer the repo the command targets via `-C <path>`, else the hook's own cwd.
    $repoPath = $null
    if ($cmd -match 'git\s+-C\s+"([^"]+)"') { $repoPath = $Matches[1] }
    elseif ($cmd -match "git\s+-C\s+'([^']+)'") { $repoPath = $Matches[1] }
    elseif ($cmd -match 'git\s+-C\s+(\S+)') { $repoPath = $Matches[1] }

    try {
        if ($repoPath) { $branch = (git -C $repoPath rev-parse --abbrev-ref HEAD 2>$null) }
        else { $branch = (git rev-parse --abbrev-ref HEAD 2>$null) }
    } catch {
        exit 0  # not a git repo / git unavailable -- stay out of the way
    }

    $branch = ($branch | Out-String).Trim()
    if ($branch -in @('main', 'master')) {
        Deny @"
Refused: you are on '$branch' and REPO_RULES.md requires branching before any commit or push.
Create a branch first, then re-run:
  git switch -c <type>/<short-desc>   # e.g. feat/add-export, fix/null-on-empty-input
Then commit/push on that branch and open a PR.

Note: merging a reviewed, green PR into main is allowed and is a different act.
Committing directly to main is not.
"@
    }
}

# ---------------------------------------------------------------------------
# 3. Review receipt  --  gh pr create
# ---------------------------------------------------------------------------
# AGENTS.md requires the diff to be critiqued by a reviewer agent before a PR opens.
# The reviewer's run leaves .claude/review/receipt.json naming the commit it read.
# This checks that a receipt exists AND matches the exact commit being submitted.
#
# Honest limitation: this forces the review to HAPPEN. It cannot force the agent to
# act on what the review said. That part stays honor-system.
if ($cmdClean -match '\bgh\s+pr\s+create\b') {
    try {
        $root = (git rev-parse --show-toplevel 2>$null | Out-String).Trim()
        $head = (git rev-parse HEAD 2>$null | Out-String).Trim()
    } catch {
        exit 0  # can't resolve the repo -- stay out of the way
    }

    if ($root -and $head) {
        $receiptPath = Join-Path $root '.claude/review/receipt.json'

        if (-not (Test-Path $receiptPath)) {
            Deny @"
Refused: no review receipt found at .claude/review/receipt.json.

AGENTS.md requires a reviewer agent to critique the diff before the PR is opened.
Do this now:
  1. Launch a reviewer subagent and give it the full diff for this branch.
  2. Fix what it finds that is valid.
  3. Write .claude/review/receipt.json:
       { "sha": "$head", "reviewedAt": "<ISO-8601>", "findings": "<summary>" }
  4. Record in the PR body what you pushed back on and why.
"@
        }

        try {
            $receipt = Get-Content $receiptPath -Raw | ConvertFrom-Json
        } catch {
            Deny "Refused: .claude/review/receipt.json exists but is not valid JSON. Re-run the reviewer and rewrite it."
        }

        $reviewedSha = [string]$receipt.sha
        if ($reviewedSha -ne $head) {
            Deny @"
Refused: the review receipt is stale.

  reviewed: $reviewedSha
  current:  $head

The code changed after it was reviewed, so what you're about to submit has not been
looked at. This is expected when you commit fixes the reviewer asked for -- just
re-run the reviewer on the current HEAD and rewrite the receipt. It's cheap.
"@
        }
    }
}

# ---------------------------------------------------------------------------
# 4 & 5. Merge gate + authority ceiling  --  gh pr merge
# ---------------------------------------------------------------------------
if ($cmdClean -match '\bgh\s+pr\s+merge\b') {

    # --admin bypasses required checks. Never legitimate here.
    if ($cmdClean -match '--admin\b') {
        Deny "Refused: --admin bypasses the checks that make self-merging safe. Fix what's red instead."
    }

    # `gh pr merge 38` targets a number; bare `gh pr merge` uses the current branch.
    $prRef = $null
    if ($cmdClean -match '\bgh\s+pr\s+merge\s+(\d+)') { $prRef = $Matches[1] }

    $viewArgs = @('pr', 'view')
    if ($prRef) { $viewArgs += $prRef }
    $viewArgs += @('--json', 'statusCheckRollup,files,number,title')

    $info = $null
    try {
        $json = & gh @viewArgs 2>$null
        if ($json) { $info = ($json | Out-String) | ConvertFrom-Json }
    } catch {
        $info = $null
    }

    # FAIL CLOSED: unable to read the PR means unable to prove it's safe to merge.
    if (-not $info) {
        Deny @"
Refused: couldn't read this PR's status from GitHub, so the merge gate can't verify it.

Check `gh auth status` and `gh pr view`. Do not route around this by merging in the
web UI -- if the gate can't see the PR, nobody has confirmed the checks are green.
"@
    }

    # --- 5. Authority ceiling ---------------------------------------------
    # The agent may propose rule changes; only Paul ratifies them. Without this,
    # merge power is self-amplifying: the agent could merge a PR widening its own
    # permissions.
    $governance = @(
        '^AGENTS\.md$',
        '^CLAUDE\.md$',
        '^GEMINI\.md$',
        '^REPO_RULES\.md$',
        '^\.claude/',
        '^\.cursor/',
        '^lefthook\.yml$',
        '^\.gitleaks\.toml$',
        '^\.github/workflows/',
        '^scripts/hooks/'
    )

    $touched = @()
    foreach ($f in $info.files) {
        $p = [string]$f.path
        foreach ($pattern in $governance) {
            if ($p -match $pattern) { $touched += $p; break }
        }
    }

    if ($touched.Count -gt 0) {
        $list = ($touched | Select-Object -Unique | ForEach-Object { "  - $_" }) -join "`n"
        Deny @"
Refused: this PR changes the rules that govern you, so it is Paul's to merge -- not yours.

Governance files touched:
$list

This is the ceiling on your own authority: you may propose and argue for a rule
change, but you may not ratify one. Post the PR link and let Paul decide.
"@
    }

    # --- 4. Merge gate: every check must be green --------------------------
    $checks = @($info.statusCheckRollup)
    if ($checks.Count -eq 0) {
        Deny @"
Refused: PR #$($info.number) has no status checks reported yet.

Either CI hasn't started, or it isn't configured for this branch. Wait for it, then
re-check with `gh pr checks`. Merging unverified work defeats the point of the gate.
"@
    }

    foreach ($c in $checks) {
        $name = if ($c.name) { $c.name } else { $c.context }

        # A CheckRun still running has status != COMPLETED. Don't merge mid-flight.
        if ($c.status -and $c.status -ne 'COMPLETED') {
            Deny "Refused: check '$name' is still running ($($c.status)). Wait for it to finish, then merge."
        }

        # CheckRun uses .conclusion; the older StatusContext type uses .state.
        $state = if ($c.conclusion) { [string]$c.conclusion } else { [string]$c.state }

        if ($state -notin @('SUCCESS', 'NEUTRAL', 'SKIPPED')) {
            Deny @"
Refused: check '$name' is $state. Never merge red.

Fix the underlying failure and push again. If the check is wrong rather than the code,
say so explicitly and let Paul make the call -- don't merge around it.
"@
        }
    }
}

exit 0
