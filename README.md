# Claude Voice

Hands-free voice conversation with Claude Code on Peter's Mac. Talk; a pause sends; Claude
thinks; the answer is spoken; the mic reopens. No record button, no play button, no typing.

Start the window:   ./start.sh          (first run: click Allow on the microphone dialog)
Self-test:          .venv/bin/python tests/selftest.py [--no-brain]
Phone receiver:     ./install_receiver.sh        (login job; the iPhone Shortcut talks to it)
Remote Control:     ./install_remote_control.sh  (login job; text door for the Claude app)
iPhone shortcut:    .venv/bin/python make_shortcut.py  -> open "Talk to Claude.shortcut" once

Pieces: whisper-server (small model, kept loaded) for speech to text; `claude -p --resume`
headless thread (shared by window and phone, file-locked); Hermes voice chain (Piper now,
Jenny when Microsoft allows it again; Meijia for Mandarin); Textual window; stdlib HTTP receiver.
State lives in ~/.claude_voice (session id, receiver token, transcript log).

Spoken commands: "stop" / "wait" cut Claude off · "go to sleep" · "hey Claude" wakes ·
"open mic" / "tap to talk" switch modes · "goodbye" files a memory note and closes.
Keys in the window: Space (talk in tap mode / interrupt), M mode, S sleep, N new thread, Q quit.
