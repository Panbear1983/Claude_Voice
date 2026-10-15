"""Build the iPhone side: a signed "Talk to Claude" Shortcut file.

The shortcut loops: dictate (stops on a pause) -> POST to the Mac receiver -> speak the
reply -> repeat. Open the produced file once on the Mac (Shortcuts asks "Add Shortcut");
iCloud then syncs it to the iPhone.

  .venv/bin/python make_shortcut.py            # writes 'Talk to Claude.shortcut' here + ~/Desktop/Misc
"""
from __future__ import annotations

import os
import plistlib
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import settings as S

REPEATS = 300          # one tap gives up to 300 exchanges
TAILSCALE = shutil.which("tailscale") or "/opt/homebrew/bin/tailscale"
TAILSCALE_IP = os.environ.get("CLAUDE_VOICE_MAC_IP") or (
    subprocess.run([TAILSCALE, "ip", "-4"], capture_output=True, text=True).stdout.strip().splitlines() or [""])[0]
if not TAILSCALE_IP:
    sys.exit("No Tailscale address found. Install Tailscale and sign in, or set CLAUDE_VOICE_MAC_IP.")
URL = f"http://{TAILSCALE_IP}:{S.RECEIVER_PORT}/ask"
TOKEN = S.RECEIVER_TOKEN_FILE.read_text().strip()


def text(value: str) -> dict:
    return {"Value": {"string": value, "attachmentsByRange": {}}, "WFSerializationType": "WFTextTokenString"}


def ref(output_uuid: str, output_name: str) -> dict:
    return {"Value": {"string": "￼",
                      "attachmentsByRange": {"{0, 1}": {"OutputUUID": output_uuid, "OutputName": output_name,
                                                        "Type": "ActionOutput"}}},
            "WFSerializationType": "WFTextTokenString"}


def dictionary(items: list[tuple[str, dict]]) -> dict:
    return {"Value": {"WFDictionaryFieldValueItems": [
        {"WFItemType": 0, "WFKey": text(k), "WFValue": v} for k, v in items]},
        "WFSerializationType": "WFDictionaryFieldValue"}


def build() -> dict:
    group = str(uuid.uuid4())
    dictate_uuid = str(uuid.uuid4())
    url_uuid = str(uuid.uuid4())
    value_uuid = str(uuid.uuid4())
    actions = [
        {"WFWorkflowActionIdentifier": "is.workflow.actions.repeat.count",
         "WFWorkflowActionParameters": {"GroupingIdentifier": group, "WFControlFlowMode": 0, "WFRepeatCount": REPEATS}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.dictatetext",
         "WFWorkflowActionParameters": {"UUID": dictate_uuid, "WFDictateTextStopListening": "After Pause"}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
         "WFWorkflowActionParameters": {
             "UUID": url_uuid, "WFURL": URL, "WFHTTPMethod": "POST", "WFHTTPBodyType": "JSON",
             "ShowHeaders": True,
             "WFHTTPHeaders": dictionary([("X-Token", text(TOKEN))]),
             "WFJSONValues": dictionary([("text", ref(dictate_uuid, "Dictated Text"))]),
         }},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
         "WFWorkflowActionParameters": {"UUID": value_uuid, "WFGetDictionaryValueType": "Value",
                                        "WFDictionaryKey": "reply",
                                        "WFInput": {"Value": {"OutputUUID": url_uuid, "OutputName": "Contents of URL",
                                                              "Type": "ActionOutput"},
                                                    "WFSerializationType": "WFTextTokenAttachment"}}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.speaktext",
         "WFWorkflowActionParameters": {"WFSpeakTextWait": True,
                                        "WFText": ref(value_uuid, "Dictionary Value")}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.repeat.count",
         "WFWorkflowActionParameters": {"GroupingIdentifier": group, "WFControlFlowMode": 2}},
    ]
    return {
        "WFWorkflowClientVersion": "2605.0.5",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowHasOutputFallback": False,
        "WFWorkflowHasShortcutInputVariables": False,
        "WFWorkflowIcon": {"WFWorkflowIconStartColor": 4282601983, "WFWorkflowIconGlyphNumber": 59511},
        "WFWorkflowImportQuestions": [],
        "WFWorkflowInputContentItemClasses": [],
        "WFWorkflowTypes": ["NCWidget", "WatchKit"],
        "WFWorkflowActions": actions,
    }


def main() -> None:
    here = Path(__file__).resolve().parent
    raw = here / "Talk to Claude.unsigned.shortcut"
    signed = here / "Talk to Claude.shortcut"
    with open(raw, "wb") as fh:
        plistlib.dump(build(), fh)
    r = subprocess.run(["/usr/bin/shortcuts", "sign", "--mode", "anyone", "--input", str(raw), "--output", str(signed)],
                       capture_output=True, text=True)
    raw.unlink(missing_ok=True)
    if r.returncode != 0 or not signed.exists():
        print("signing failed:", r.stderr.strip() or r.stdout.strip())
        sys.exit(1)
    misc = Path.home() / "Desktop/Misc"
    if misc.is_dir():
        shutil.copy(signed, misc / signed.name)
    print(f"built {signed}  (receiver {URL})")


if __name__ == "__main__":
    main()
