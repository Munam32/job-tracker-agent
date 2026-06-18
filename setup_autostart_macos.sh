#!/usr/bin/env bash
# ============================================================
# setup_autostart_macos.sh — Install Job Tracker daily launchd agent
#
# Creates a launchd plist in ~/Library/LaunchAgents that runs
# scheduler.py --once daily at 12:00 PM local time.
#
# Usage: bash setup_autostart_macos.sh
# ============================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
SCRIPT_PATH="$PROJECT_DIR/scheduler.py"
LOG_DIR="$PROJECT_DIR/logs"
PLIST_NAME="com.user.jobtracker.daily"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

# ─────────────────────────────────────────────
# Validate
# ─────────────────────────────────────────────
if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "❌ Virtual environment not found at: $VENV_PYTHON"
    echo "   Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

if [[ ! -f "$SCRIPT_PATH" ]]; then
    echo "❌ scheduler.py not found at: $SCRIPT_PATH"
    exit 1
fi

# ─────────────────────────────────────────────
# Create logs directory
# ─────────────────────────────────────────────
mkdir -p "$LOG_DIR"

# ─────────────────────────────────────────────
# Write plist file
# ─────────────────────────────────────────────
cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>

    <key>ProgramArguments</key>
    <array>
        <string>$VENV_PYTHON</string>
        <string>$SCRIPT_PATH</string>
        <string>--once</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>12</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>RunAtLoad</key>
    <false/>

    <key>StandardOutPath</key>
    <string>$LOG_DIR/scheduler.log</string>

    <key>StandardErrorPath</key>
    <string>$LOG_DIR/scheduler_error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:$PROJECT_DIR/venv/bin</string>
    </dict>
</dict>
</plist>
EOF

echo "✅ launchd plist created: $PLIST_PATH"

# ─────────────────────────────────────────────
# Load into launchd
# ─────────────────────────────────────────────
launchctl load "$PLIST_PATH"
echo "✅ launchd agent loaded: $PLIST_NAME"

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
echo ""
echo "   Runs daily at 12:00 PM local time"
echo "   Python: $VENV_PYTHON"
echo "   Script: $SCRIPT_PATH"
echo "   Logs:   $LOG_DIR/scheduler.log"
echo ""
echo "To check status:"
echo "  launchctl list | grep $PLIST_NAME"
echo ""
echo "To uninstall:"
echo "  launchctl unload $PLIST_PATH && rm $PLIST_PATH"
