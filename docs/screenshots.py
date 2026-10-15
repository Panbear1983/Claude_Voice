"""Regenerate the README pictures from the real window, headlessly (no mic, no screen).

  .venv/bin/python docs/screenshots.py          # writes docs/img/*.svg

The conversation replayed here (docs/demo_conversation.json) was recorded from real
Claude turns on a throwaway thread. PNG/GIF versions are made by docs/render_images.py.
"""
from __future__ import annotations

import asyncio
import html
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("CLAUDE_VOICE_STATE", tempfile.mkdtemp(prefix="cv-shots-"))

import engine  # noqa: E402

engine.Engine.start = lambda self: None          # no mic, no whisper
from app import ClaudeVoice  # noqa: E402
from rich.cells import cell_len  # noqa: E402

OUT = ROOT / "docs/img"
SIZE = (96, 22)
DEMO = json.loads((ROOT / "docs/demo_conversation.json").read_text())


_TEXT = re.compile(r'(<text [^>]*?textLength=")([0-9.]+)("[^>]*>)([^<]*)(</text>)')


def fix_wide_chars(svg: str) -> str:
    """Textual's SVG export sizes each text run by character count, so Chinese (two cells
    per character) is squeezed into half its width. Re-measure every run in cells."""
    cell = next(float(m.group(2)) / len(html.unescape(m.group(4)))
                for m in _TEXT.finditer(svg) if html.unescape(m.group(4)).isascii() and m.group(4))
    return _TEXT.sub(lambda m: f"{m.group(1)}{cell_len(html.unescape(m.group(4))) * cell:g}"
                               f"{m.group(3)}{m.group(4)}{m.group(5)}", svg)


async def shoot() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    app = ClaudeVoice()
    async with app.run_test(size=SIZE) as pilot:

        async def snap(name: str, state: str, level: float) -> None:
            app.engine.mic.level = level
            app._apply("state", state)
            await pilot.pause(0.35)                      # let the mic meter tick
            (OUT / f"{name}.svg").write_text(fix_wide_chars(app.export_screenshot()), encoding="utf-8")

        first, second = DEMO
        await snap("01_listening", "listening", 40)
        await snap("02_hearing", "hearing", 1350)
        app._apply("you", first["you"])
        app._apply("progress", first["progress"])
        app._apply("status", first["status"])
        await snap("03_thinking", "thinking", 30)
        app._apply("claude", first["claude"])
        await snap("04_speaking", "speaking", 380)
        app._apply("you", second["you"])
        app._apply("claude", second["claude"])
        await snap("05_mandarin", "speaking", 300)
        await snap("06_asleep", "asleep", 25)


if __name__ == "__main__":
    asyncio.run(shoot())
    print("\n".join(sorted(p.name for p in OUT.glob("*.svg"))))
