#!/bin/bash
# Installs the phone receiver as a login job (launchd) so the iPhone Shortcut always has
# something to talk to while the Mac is awake. Re-run any time; it reloads.
set -u
cd "$(dirname "$0")" || exit 1
label=com.peter.voice-desk-receiver
plist="$HOME/Library/LaunchAgents/$label.plist"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/.voice_desk"
cat > "$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key><array><string>$PWD/start_receiver.sh</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>WorkingDirectory</key><string>$PWD</string>
  <key>StandardOutPath</key><string>$HOME/.voice_desk/receiver.log</string>
  <key>StandardErrorPath</key><string>$HOME/.voice_desk/receiver.log</string>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin</string>
    <key>HOME</key><string>$HOME</string>
  </dict>
</dict></plist>
PLIST
launchctl bootout "gui/$(id -u)/$label" 2>/dev/null
launchctl bootstrap "gui/$(id -u)" "$plist" && echo "receiver installed and running ($label)"
