# Claude Voice

Talk to Claude Code out loud, hands-free, from the Mac or the iPhone.

You speak. When you pause for a second and a half, what you said is sent. Claude works on
it (it can read files, run commands, search the web, the same as a normal Claude Code
session), the answer is spoken back to you, and the microphone opens again for your next
sentence. There is no record button, no play button, and nothing to type.

The Mac window and the iPhone share **one conversation**, so you can start a thought at
the desk and finish it from the phone.

```
   you talk ──► pause 1.5 s ──► speech to text ──► Claude Code ──► spoken reply ──┐
       ▲                         (whisper, local)   (one thread)   (Piper / Meijia) │
       └──────────────────────── microphone reopens ◄──────────────────────────────┘
```

---

## Contents

- [What you need](#what-you-need)
- [Setup](#setup)
- [Everyday use](#everyday-use)
- [The phone](#the-phone)
- [How it works](#how-it-works)
- [Where things are kept](#where-things-are-kept)
- [Changing behaviour](#changing-behaviour)
- [Safety and privacy](#safety-and-privacy)
- [Troubleshooting](#troubleshooting)
- [Testing](#testing)
- [File map](#file-map)

---

## What you need

Everything runs on the Mac. Nothing is sent anywhere except the text of your question
to Claude.

| Piece | What it does | How it got here |
|---|---|---|
| Python 3.11 + `.venv` | runs the app | `uv venv` (see Setup) |
| `whisper-server` + `ggml-small.bin` | turns your voice into text, locally | `brew install whisper-cpp`; model in `~/.local/share/whisper-models/` |
| `claude` CLI, logged in | the brain | Claude Code subscription; no API key |
| `ffmpeg` | converts audio between formats | `brew install ffmpeg` |
| Hermes voice chain (optional) | the English voice (Piper; Jenny when Microsoft allows) | `~/.hermes/profiles/orchestrator/scripts/tts_jenny_or_mac.sh` |
| Mac voices | Mandarin (Meijia) and the last-resort English voice | built into macOS |
| Tailscale (phone only) | lets the iPhone reach the Mac from anywhere | Tailscale on both devices |

If the Hermes voice script is missing, English replies fall back to the plain Mac voice,
so the loop never goes silent.

## Setup

```bash
cd ~/GitHub/Claude_Voice
uv venv .venv --python 3.11
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python tests/selftest.py --no-brain     # checks mic logic, whisper, voices, window
```

The first time the window opens, macOS asks whether Terminal may use the microphone.
Click **Allow**. That is the only permission it needs.

## Everyday use

**Double-click `start.sh`.** A small window opens with a coloured light and a running
transcript. Wait for "I'm listening", then just talk.

| Light | Meaning |
|---|---|
| green, *listening* | waiting for you to speak |
| darker green, *hearing you* | it has picked up your voice |
| orange, *thinking* | Claude is working; every 10 s it says what it is doing ("still reading files") |
| blue, *speaking* | the answer is being read out |
| grey, *asleep* | nothing said for 60 s; say "hey Claude" to wake it |

Under the mode label there is a live microphone meter, so a dead mic is obvious at once.

### Things you can say

| Say | What happens |
|---|---|
| "stop", "wait", "hold on", 「等一下」 | cuts Claude off mid-sentence (or just start talking over it) |
| "go to sleep", 「休息」 | pauses listening until "hey Claude" |
| "hey Claude …" | wakes it; anything after the wake word is sent as your question |
| "open mic" / "tap to talk" | switches listening mode |
| "use Opus", "switch to Sonnet", "use Haiku", "use Fable" | changes the model from the next question on |
| "which model" | says which model is in use |
| "think deep", "quick mode", "max effort", "normal mode" | how hard Claude thinks: quick / normal / deep / max |
| "which effort" | says the current effort |
| "goodbye", 「再見」 | Claude files one memory note about the session, says goodbye, window closes |

Ending a sentence with "over" or "send" is allowed and the word is dropped. You can speak
English or Mandarin; Mandarin answers come back in the Meijia (Taiwan) voice.

### Keys

| Key | Action |
|---|---|
| Space | in tap mode: start / send. In open-mic mode: interrupt the reply |
| M | open mic ⇄ tap to talk |
| S | sleep / wake |
| N | start a fresh conversation (Claude forgets this thread) |
| Q | quit |

Open mic is the default. Tap mode is for noisy rooms: press Space, talk, press Space.

## The phone

Two separate doors, both installed once and then started automatically at login.

**1. Voice, through an iPhone Shortcut ("Hey Siri, Talk to Claude").**

```bash
./install_receiver.sh                      # small web receiver on port 8765, runs at login
.venv/bin/python make_shortcut.py          # builds and signs "Talk to Claude.shortcut"
```

Open the `.shortcut` file once on the iPhone (Shortcuts → Add Shortcut). If iCloud does
not sync it, send the file to yourself (Telegram works) and choose "Open in Shortcuts".
The phone must be signed in to Tailscale.

The Shortcut loops up to 300 times: dictate (stops when you pause) → send the text to
the Mac → read the reply aloud → listen again. It joins the same conversation as the
Mac window.

**2. Text, through the Claude app.**

```bash
./install_remote_control.sh                # keeps a "Peter Mac" Remote Control session alive
```

The Claude app on the phone then always finds a session on this Mac to type into.

## How it works

Each stage is one small file and can be tested on its own.

1. **Listening** (`audio.py`). The microphone stays open. Every 30 ms the loudness is
   compared with a background-noise level that keeps re-measuring itself while you are
   quiet. A quarter second of loud sound starts a recording; 0.6 s of audio from just
   before is kept so the first word is not clipped; 1.5 s of quiet ends it. Anything
   under 0.4 s is treated as a cough. No speech library or model is used here.

2. **Speech to text** (`stt.py`). `whisper-server` is started once and kept loaded, so a
   turn costs about 1.2–1.6 s instead of the ~9 s it takes to reload the model each
   time. Language is detected automatically. Whisper's habit of inventing "Thank you."
   or "Thanks for watching" out of silence is filtered out.

3. **Claude** (`brain.py`). Each turn runs `claude -p --resume <thread>` in your home
   folder, so every project is reachable. A voice-specific instruction tells Claude to
   answer in one to four spoken sentences, with no code, paths or links; long detail goes
   to `~/.claude_voice/detail.md` instead. The thread id is saved so the next turn, from
   either the Mac or the phone, continues the same conversation. A file lock makes the
   phone and the window take turns. While Claude works, the tool it is using becomes a
   spoken status line every 10 s. Model and effort changes are handled here without a
   Claude call.

4. **Speaking** (`tts.py`). Markdown, code blocks and links are stripped so nothing
   unreadable is read aloud. English goes through the Hermes chain in the order
   "piper mac" (Jenny is skipped while Microsoft refuses it; trying her first cost ~6 s
   per reply). Mandarin goes to the Mac's Meijia voice. Playback can be killed instantly.

5. **Interrupting** (`audio.py`, `engine.py`). While a reply plays, the mic keeps
   listening. Because the speakers leak into the mic, it measures how loud the playback
   sounds for the first 0.7 s and then only counts you as talking if you are clearly
   louder than that for half a second.

6. **The loop and the window** (`engine.py`, `app.py`). `engine.py` runs the cycle on a
   background thread and knows nothing about the screen; `app.py` is a Textual window
   that shows the light, transcript and mic meter.

7. **The phone receiver** (`receiver.py`). A tiny web server with two addresses:
   `GET /health` and `POST /ask {"text": …}` which returns `{"reply": …}`. Every request
   must carry the token.

**Typical timings on this Mac:** speech to text 1.2–1.6 s, simple Claude turn 4–11 s,
a turn that digs through files ~20 s, Piper voice ~2.7 s, Meijia ~4 s.

## Where things are kept

Nothing personal lives in the repo. Everything the app remembers is in `~/.claude_voice/`:

| File | Holds |
|---|---|
| `session_id` | the shared conversation thread |
| `model`, `effort` | your spoken model / effort choice |
| `receiver_token` | the phone's password (created on first run, owner-only) |
| `transcript.log` | every question and answer, time-stamped |
| `detail.md` | long answers Claude chose not to read aloud |
| `window.lock`, `turn.lock` | "window is open" and "a turn is running" markers |
| `receiver.log`, `remote-control.log` | background job logs |

Set `CLAUDE_VOICE_STATE` to use a different folder (the self-test does this).

## Changing behaviour

All tunables are plain constants in `settings.py`. The ones worth knowing:

| Setting | Default | Meaning |
|---|---|---|
| `SILENCE_SEND_SEC` | 1.5 | how long a pause counts as "send" |
| `SLEEP_AFTER_SEC` | 60 | quiet time before it goes to sleep |
| `WHISPER_MODEL` | small | speech model; large-v3-turbo is more accurate but ~3× slower |
| `TTS_ORDER` | `piper mac` | put `edge` first again when Jenny works |
| `DEFAULT_MODEL` / `DEFAULT_EFFORT` | Fable / medium | used until you say otherwise |
| `RECEIVER_PORT` | 8765 | phone receiver port |

Environment overrides: `CLAUDE_VOICE_STATE`, `CLAUDE_VOICE_TTS_ORDER`,
`CLAUDE_VOICE_CLAUDE_BIN`, `CLAUDE_VOICE_WHISPER_PORT`, `CLAUDE_VOICE_RECEIVER_HOST`,
`CLAUDE_VOICE_RECEIVER_PORT`.

## Safety and privacy

- **Claude runs with full permissions** (`bypassPermissions`), the same as a trusted
  terminal session: it does not stop to ask before running a command. That is what makes
  a hands-free loop possible, and it is why the next two points matter.
- **The phone receiver is protected only by its token.** It listens on every network the
  Mac is on (home Wi-Fi and Tailscale). Anyone who has the token and can reach the Mac
  could talk to Claude as you. The token lives only in `~/.claude_voice/receiver_token`
  and inside the signed Shortcut file; both are kept out of git. To limit it to
  Tailscale only, set `CLAUDE_VOICE_RECEIVER_HOST` to the Mac's Tailscale address. To
  change it, delete the token file, restart the receiver and rebuild the Shortcut.
- **Your voice never leaves the Mac.** Speech to text is local; only the transcribed
  text goes to Claude.
- **Two guards stop the Mac talking to itself:**
  - Every voice turn sets `CLAUDE_VOICE_LOOP=1`. The global "read the answer aloud" and
    memory-save Stop hooks skip when they see it; otherwise every reply would be spoken
    twice and memory checkpoints would block a turn.
  - While the window is open (`window.lock` held), the read-aloud hook stays silent in
    **every** Claude session. Without this the open mic heard another session's spoken
    answer and sent it to Claude as if you had said it.

  Do not remove either guard.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Mic meter stays at 0 | Terminal has no microphone permission: System Settings → Privacy & Security → Microphone |
| "Claude Voice is already open in another window" | only one window at a time; close the other one |
| Light stuck on *hearing you* | room too loud for open mic; press M for tap mode |
| It answers things you did not say | something else on the Mac is speaking; close it or use tap mode |
| Phone Shortcut fails | Tailscale off on the phone, receiver not running (`curl http://<mac-tailscale-ip>:8765/health`), or a long turn ran past the Shortcut's time limit |
| A new, empty conversation started on its own | you opened the voice thread with `claude --resume` and left it open; the loop starts a fresh thread when the old one is busy. Read it, then quit |
| Replies slow to start speaking | check `TTS_ORDER`; a refused Jenny voice costs ~6 s before Piper takes over |
| Restarting a login job says "Input/output error" | wait 3 s between unloading and loading it |

## Testing

```bash
.venv/bin/python tests/selftest.py              # every stage, including two real Claude turns
.venv/bin/python tests/selftest.py --no-brain   # everything except Claude (spends no tokens)
```

It needs no microphone and no screen. It checks the silence detector on synthetic audio,
whisper on a spoken sample, both voices, that Claude remembers a code word across two
turns on one thread, and that the window opens and the M key switches mode.

## File map

| File | Role |
|---|---|
| `start.sh` | double-click launcher for the window |
| `app.py` | the window (light, transcript, mic meter, keys) |
| `engine.py` | the listen → think → speak loop and spoken commands |
| `audio.py` | microphone, silence detection, talk-over detection |
| `stt.py` | whisper-server control and transcript cleanup |
| `brain.py` | Claude thread, model / effort switching, spoken status |
| `tts.py` | read-aloud cleanup, voice selection, playback |
| `settings.py` | every tunable in one place |
| `receiver.py`, `start_receiver.sh`, `install_receiver.sh` | phone receiver and its login job |
| `make_shortcut.py` | builds the signed iPhone Shortcut |
| `install_remote_control.sh` | Remote Control login job for the Claude app |
| `tests/selftest.py` | headless end-to-end check |
| `AGENTS.md`, `CLAUDE.md` | rules for AI agents working on this repo |
