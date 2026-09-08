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

## Where the compute runs — start on the laptop GPU

Two candidate machines: the owner's laptop (NVIDIA RTX 3060, 6 GB VRAM) and the always-on
Minisforum mini PC (CPU/RAM unverified; its SSH accepts git only, so it could not be inspected).

**Correction to an earlier assessment in this file's first revision:** the laptop was ruled out
on the grounds that it breaks "works away from home". That was wrong. Tailscale is a mesh, so
the phone reaches the laptop directly wherever both are, provided both are connected. The
actual limitation is narrower — **the laptop must be awake**. A sleeping laptop cannot be woken
over the network to serve a request.

On quality the GPU wins outright, and that matters more than latency here. 6 GB fits the
largest, most accurate Whisper model with a roughly one-second turnaround for a short clip.
The mini PC's CPU would force a smaller model, with weaker punctuation and more misheard
words — which is precisely the owner's stated complaint, so it is not a minor concession.

**Decision: start on the laptop GPU.** The choice is cheap to reverse: the hub, the endpoint
contract, the Android keyboard configuration and the security wall are identical either way,
and only the model's location differs. A week of real use will show whether the sleeping-laptop
problem bites in practice. If it does, move the model to the mini PC and accept a smaller one.

The cost of keeping a gaming laptop awake continuously — fan noise, heat, and a battery held
at full charge — is the reason not to make that the permanent answer without testing first.

## Not yet decided

- Whether Google owner sign-in is still warranted once there is no spendable key or quota
  behind it (the meaningful wall becomes Tailscale plus revocable device keys).
- Which Android keyboard app to standardise on; none has been tested.
- Whether text-to-speech returns later as a local model.
