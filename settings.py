"""Claude Voice — one place for every tunable.

Plain constants, no config file: Peter asked for a few presets, not a page of knobs.
The two presets that matter are the listening mode (open mic / tap to talk) and the
sleep timer; both are switchable from inside the window.
"""
from __future__ import annotations

import os
from pathlib import Path

HOME = Path.home()
REPO = Path(__file__).resolve().parent
STATE_DIR = Path(os.environ.get("CLAUDE_VOICE_STATE", HOME / ".claude_voice"))
STATE_DIR.mkdir(parents=True, exist_ok=True)

# ---- microphone / silence detection -------------------------------------------------
SAMPLE_RATE = 16_000            # whisper wants 16 kHz mono
BLOCK_MS = 30                   # one analysis slice
BLOCK = SAMPLE_RATE * BLOCK_MS // 1000
PRE_ROLL_SEC = 0.6              # audio kept from before speech was detected
SPEECH_START_SEC = 0.25         # how long sound must stay loud before we call it speech
SILENCE_SEND_SEC = 1.5          # Peter's pause that acts as "send"
MAX_UTTERANCE_SEC = 90          # hard stop so a stuck mic cannot record forever
MIN_SPEECH_SEC = 0.4            # anything shorter is a cough or a click
NOISE_FLOOR_START = 150.0       # int16 RMS guess before calibration
SPEECH_OVER_FLOOR = 3.0         # speech = louder than floor * this (and above MIN_SPEECH_RMS)
MIN_SPEECH_RMS = 350.0
BARGE_IN_OVER_FLOOR = 4.0       # while Claude speaks, the mic hears the speakers too, so be stricter
BARGE_IN_SEC = 0.5

# ---- sleep / wake --------------------------------------------------------------------
SLEEP_AFTER_SEC = 60            # no speech for this long -> grey light, wake word needed
WAKE_WORDS = ("hey claude", "hey, claude", "claude", "克勞德", "克劳德")

# ---- spoken commands (matched after lowercasing and stripping punctuation) ------------
STOP_WORDS = {"stop", "wait", "hold on", "stop talking", "shut up", "quiet", "等一下", "停"}
GOODBYE_WORDS = {"goodbye", "good bye", "bye", "bye claude", "bye bye", "that's all", "that is all", "再見", "拜拜"}
SLEEP_WORDS = {"go to sleep", "sleep now", "stop listening", "休息"}
OPEN_MIC_WORDS = {"open mic", "open microphone", "hands free"}
TAP_MODE_WORDS = {"push to talk", "tap to talk", "tap mode"}
TRAILING_SEND_WORDS = ("over", "over.", "send", "send.")

# ---- speech to text ------------------------------------------------------------------
WHISPER_SERVER = "/opt/homebrew/bin/whisper-server"
WHISPER_MODEL = HOME / ".local/share/whisper-models/ggml-small.bin"   # 1.2 s per turn; large-v3-turbo is 4.5 s
WHISPER_PORT = int(os.environ.get("CLAUDE_VOICE_WHISPER_PORT", "8178"))
WHISPER_THREADS = 8
WHISPER_LANGUAGE = "auto"       # English and Mandarin both land correctly

# whisper invents these on silence / breaths; drop them.
WHISPER_HALLUCINATIONS = {
    "", "thank you.", "thank you", "thanks for watching.", "thanks for watching", "you", "you.",
    "bye.", "bye", "[blank_audio]", "(silence)", "[silence]", "[music]", "(music)", "字幕由amara.org社群提供",
    "請不吝點贊 訂閱 轉發 打賞支持明鏡與點點欄目", "謝謝觀看", "谢谢观看",
}

# ---- text to speech ------------------------------------------------------------------
# Hermes' voice chain: edge Jenny (refused by Microsoft since 2026-10-10) -> Piper -> Mac voice.
TTS_CHAIN = HOME / ".hermes/profiles/orchestrator/scripts/tts_jenny_or_mac.sh"
# "piper mac" for now: trying Jenny first costs ~6 s per reply while Microsoft keeps refusing her.
# Put "edge" back in front when Jenny works again.
TTS_ORDER = os.environ.get("CLAUDE_VOICE_TTS_ORDER", "piper mac")
TTS_VOICE_EN = "en-US-JennyNeural"
TTS_VOICE_ZH_MAC = "Meijia"      # Taiwan Mandarin, the voice Peter uses elsewhere
AFPLAY = "/usr/bin/afplay"
FFMPEG = "/opt/homebrew/bin/ffmpeg"
STATUS_EVERY_SEC = 10           # spoken "still working" while Claude thinks

# ---- the brain -----------------------------------------------------------------------
CLAUDE_BIN = os.environ.get("CLAUDE_VOICE_CLAUDE_BIN", "claude")
CLAUDE_CWD = HOME               # the thread runs in Peter's home, so every repo is reachable
CLAUDE_TURN_TIMEOUT_SEC = 600
SESSION_FILE = STATE_DIR / "session_id"          # one thread shared by the Mac window and the phone
DEFAULT_MODEL = "claude-fable-5-1"
MODEL_FILE = STATE_DIR / "model"                 # set by voice: "use Opus", "switch to Sonnet", "which model"
DEFAULT_EFFORT = "medium"                        # voice presets: quick (low) / normal (medium) / deep (high) / max
EFFORT_FILE = STATE_DIR / "effort"               # set by voice: "think deep", "quick mode", "which effort"
TURN_LOCK_FILE = STATE_DIR / "turn.lock"
TRANSCRIPT_LOG = STATE_DIR / "transcript.log"

VOICE_SYSTEM_PROMPT = """You are talking with Peter through a live voice loop. He hears you; he is not reading a screen.
Reply the way you would speak on the phone: plain spoken English (answer in Mandarin if he spoke Mandarin), one to four short sentences, lead with the outcome.
No markdown, no bullet lists, no headings, no code blocks, no file paths, no URLs, no emojis, nothing that cannot be read aloud.
If the real answer needs code or long detail, do the work, write the detail to the file ~/.claude_voice/detail.md, and say in one sentence that the detail is in the window.
Do not ask more than one question at a time. Never end with a summary of what you just said."""

# ---- phone receiver ------------------------------------------------------------------
RECEIVER_HOST = os.environ.get("CLAUDE_VOICE_RECEIVER_HOST", "0.0.0.0")   # Tailscale + LAN; token-protected
RECEIVER_PORT = int(os.environ.get("CLAUDE_VOICE_RECEIVER_PORT", "8765"))
RECEIVER_TOKEN_FILE = STATE_DIR / "receiver_token"
