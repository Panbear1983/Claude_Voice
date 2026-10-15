#!/bin/bash
# Keeps a Remote Control server running at login, so the Claude app on the phone always
# finds a session on this Mac (text door). Re-run any time; it reloads.
set -u
label=com.peter.claude-remote-control
plist="$HOME/Library/LaunchAgents/$label.plist"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/.voice_desk"
claude_bin="$(command -v claude || echo /opt/homebrew/bin/claude)"
cat > "$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key><array>
    <string>$claude_bin</string><string>remote-control</string>
    <string>--name</string><string>Peter Mac</string>
    <string>--permission-mode</string><string>bypassPermissions</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>WorkingDirectory</key><string>$HOME</string>
  <key>StandardOutPath</key><string>/dev/null</string>
  <key>StandardErrorPath</key><string>$HOME/.voice_desk/remote-control.log</string>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin</string>
    <key>HOME</key><string>$HOME</string>
  </dict>
</dict></plist>
PLIST
launchctl bootout "gui/$(id -u)/$label" 2>/dev/null
launchctl bootstrap "gui/$(id -u)" "$plist" && echo "remote control server installed ($label)"
