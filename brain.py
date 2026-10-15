"""The brain: one headless Claude Code thread, resumed turn after turn, shared by the Mac
window and the phone receiver (a file lock serializes turns)."""
from __future__ import annotations

import fcntl
import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import settings as S

StatusCb = Callable[[str], None]

_TOOL_STATUS = {
    "Read": "still reading files",
    "Grep": "still searching the code",
    "Glob": "still looking for files",
    "Bash": "still running a command",
    "Edit": "still editing a file",
    "Write": "still writing a file",
    "WebSearch": "still searching the web",
    "WebFetch": "still reading a web page",
    "Agent": "still waiting on a helper",
}


class Brain:
    def __init__(self) -> None:
        self.session_id: Optional[str] = self._load_session()
        self.last_tool = ""
        self._proc: Optional[subprocess.Popen] = None

    # -- session bookkeeping ---------------------------------------------------------------
    def _load_session(self) -> Optional[str]:
        try:
            sid = S.SESSION_FILE.read_text().strip()
            return sid or None
        except OSError:
            return None

    def _save_session(self, sid: str) -> None:
        S.SESSION_FILE.write_text(sid)
        self.session_id = sid

    def new_thread(self) -> None:
        """Forget the running conversation (next turn starts fresh)."""
        try:
            S.SESSION_FILE.unlink()
        except OSError:
            pass
        self.session_id = None

    # -- one turn --------------------------------------------------------------------------
    def ask(self, text: str, on_status: StatusCb = lambda s: None,
            on_text: Callable[[str], None] = lambda s: None) -> str:
        """Send text, return Claude's final reply. on_status gets a short spoken-status
        phrase every STATUS_EVERY_SEC while Claude works."""
        with open(S.TURN_LOCK_FILE, "w") as lockf:
            fcntl.flock(lockf, fcntl.LOCK_EX)          # phone and window take turns
            return self._ask_locked(text, on_status, on_text)

    def _ask_locked(self, text: str, on_status: StatusCb, on_text: Callable[[str], None]) -> str:
        cmd = [S.CLAUDE_BIN, "-p", text, "--output-format", "stream-json", "--verbose",
               "--permission-mode", "bypassPermissions",
               "--append-system-prompt", S.VOICE_SYSTEM_PROMPT]
        if self.session_id:
            cmd += ["--resume", self.session_id]
        env = dict(os.environ, CLAUDE_VOICE_LOOP="1")
        self.last_tool = ""
        self._proc = subprocess.Popen(cmd, cwd=str(S.CLAUDE_CWD), env=env, text=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stop = threading.Event()
        ticker = threading.Thread(target=self._status_ticker, args=(stop, on_status), daemon=True)
        ticker.start()
        result = ""
        session_in_use = False
        try:
            assert self._proc.stdout
            for line in self._proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                t = ev.get("type")
                if t == "system" and ev.get("session_id"):
                    self._save_session(ev["session_id"])
                elif t == "assistant":
                    for block in (ev.get("message") or {}).get("content", []):
                        if block.get("type") == "tool_use":
                            self.last_tool = block.get("name", "")
                        elif block.get("type") == "text" and block.get("text"):
                            on_text(block["text"])
                elif t == "result":
                    result = ev.get("result") or ""
                    if ev.get("session_id"):
                        self._save_session(ev["session_id"])
                    if ev.get("is_error") and "in use" in result.lower():
                        session_in_use = True
            self._proc.wait(timeout=S.CLAUDE_TURN_TIMEOUT_SEC)
        finally:
            stop.set()
            err = ""
            if self._proc and self._proc.stderr:
                try:
                    err = self._proc.stderr.read()
                except Exception:
                    pass
            self._proc = None
        if session_in_use or (not result and "already in use" in err.lower()):
            # the thread is being driven elsewhere (e.g. a resumed interactive window); fork a fresh one
            self.new_thread()
            return self._ask_locked(text, on_status, on_text)
        if not result:
            tail = err.strip().splitlines()[-1] if err.strip() else "no reply"
            return f"I did not get an answer back. The error was: {tail}"
        self._log(text, result)
        return result

    def cancel(self) -> None:
        p = self._proc
        if p and p.poll() is None:
            p.terminate()

    def _status_ticker(self, stop: threading.Event, on_status: StatusCb) -> None:
        n = 0
        while not stop.wait(S.STATUS_EVERY_SEC):
            n += 1
            phrase = _TOOL_STATUS.get(self.last_tool, "still working on it")
            if n % 3 == 0:
                phrase = "still here, this one is taking a while"
            on_status(phrase)

    @staticmethod
    def _log(prompt: str, reply: str) -> None:
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(S.TRANSCRIPT_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"[{stamp}] PETER: {prompt}\n[{stamp}] CLAUDE: {reply}\n\n")
