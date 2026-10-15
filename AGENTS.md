# Claude_Voice — agent rules

Memory wing: `claude_voice` (shared mempalace, protocol at `~/.mempalace/MEMORY_PROTOCOL.md`).
Search that wing before planning; file one note under it when you finish.

What this is: a hands-free voice loop with Claude Code on Peter's Mac. Mic open -> a pause of
1.5 s sends -> whisper-server (small model, kept loaded) -> `claude -p --resume` headless thread
-> spoken reply via Hermes' voice chain (Jenny -> Piper -> Mac voice; Meijia for Mandarin) ->
mic reopens. Window = `app.py` (Textual 7.5). Phone door = `receiver.py` + an iOS Shortcut.

Standing rules:
- Peter never types in the window and never presses record or play. Keep it that way.
- Settings are a handful of presets in `settings.py`, not a config page.
- The headless thread sets `CLAUDE_VOICE_LOOP=1`; the speak-response and mempalace Stop hooks
  exit early on it. Do not remove that guard or every reply is spoken twice.
- Do not launch the window for Peter; he double-clicks `start.sh` himself.
- Never commit anything from `~/.claude_voice/` (session id, receiver token, transcript).
