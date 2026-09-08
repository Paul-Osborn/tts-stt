# Direction change under consideration — local speech-to-text, no cloud provider

**Status:** owner intent stated 2026-09-08, not yet approved as a plan. No code changed.

## What the owner asked for

Replace the cloud provider with **local models**, keep **speech-to-text only**, and drop
text-to-speech for now. It must keep working on the Android phone and from away from home.

The stated pain with Google's dictation, in the owner's words: it cuts him off before he has
finished speaking, and it does not punctuate.

## Why local speech-to-text answers that

Google's dictation is a live stream: it guesses continuously and decides on its own when the
speaker has stopped. That is the cut-off, and it is also why punctuation is poor — punctuation
depends on knowing how a sentence ends. Whisper-style models transcribe a *finished* recording,
so nothing decides when the speaker is done, and punctuation is native. The two complaints are
one design difference, not two bugs.

## What this changes in the repository

Only the engine beneath the endpoint. The `POST /v1/audio/transcriptions` contract is what
off-the-shelf Android dictation keyboards (Whisper IME, Sayboard) expect, so it must not change.

| Keep | Remove |
|---|---|
| `/v1/audio/transcriptions` and its request/response shape | `app/gemini.py` |
| Device keys, revocation, origin/host guard, session wall | Gemini key, encrypted provider vault, free-tier gate |
| Tailscale private mount, web tester, `client/desktop.py` (F8 dictation) | Quota limits (they protected a free tier that no longer applies) |
|  | `POST /v1/audio/speech` and the tester's speech half |

Net effect is deletion. The hub stops making any outbound internet call, which makes the
privacy claim in `PRD.md` true rather than qualified.

## Constraint that must change

`PRD.md` and `REPO_RULES.md` currently forbid local model installs and cap the server at
200 MB RAM. A local speech model breaks that cap. Those documents need rewriting as part of
this change, not quietly ignored.

## Open risk — where the compute runs

The owner's RTX 3060 is in the **laptop**. The always-on machine reachable from away is the
**Minisforum mini PC**, whose CPU/RAM are unverified (its SSH accepts git only, so it could not
be inspected from the laptop). Building around the GPU would silently reduce "works away from
home" to "works while the laptop is awake at home" — not acceptable.

Therefore: run on the mini PC's CPU. The open question is latency after key release, expected
in the range of a few seconds for a sentence or two. Model size is the quality/speed dial.

**Step one of any implementation is measuring real transcription latency on the mini PC**
across model sizes, before building anything on top of it.

## Not yet decided

- Whether Google owner sign-in is still warranted once there is no spendable key or quota
  behind it (the meaningful wall becomes Tailscale plus revocable device keys).
- Which Android keyboard app to standardise on; none has been tested.
- Whether text-to-speech returns later as a local model.
