#!/usr/bin/env bash
# ============================================================
# setup_autostart_linux.sh — Install Job Tracker systemd user timer
#
# Creates a systemd user service + timer that runs
# scheduler.py --once daily at 12:00 PM local time.
#
# Usage: bash setup_autostart_linux.sh
# ============================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
SCRIPT_PATH="$PROJECT_DIR/scheduler.py"
LOG_DIR="$PROJECT_DIR/logs"
SERVICE_NAME="jobtracker-daily"
SERVICE_DIR="$HOME/.config/systemd/user"

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
# Create required directories
# ─────────────────────────────────────────────
mkdir -p "$SERVICE_DIR" "$LOG_DIR"

# ─────────────────────────────────────────────
# Write service unit
# ─────────────────────────────────────────────
cat > "$SERVICE_DIR/$SERVICE_NAME.service" <<EOF
[Unit]
Description=Job Tracker Daily Email Check
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=$VENV_PYTHON $SCRIPT_PATH --once
WorkingDirectory=$PROJECT_DIR
StandardOutput=append:$LOG_DIR/scheduler.log
StandardError=append:$LOG_DIR/scheduler_error.log

[Install]
WantedBy=default.target
EOF

echo "✅ systemd service created: $SERVICE_NAME.service"

# ─────────────────────────────────────────────
# Write timer unit
# ─────────────────────────────────────────────
cat > "$SERVICE_DIR/$SERVICE_NAME.timer" <<EOF
[Unit]
Description=Run Job Tracker daily at 12:00 PM

[Timer]
OnCalendar=*-*-* 12:00:00
Persistent=true
RandomizedDelaySec=15m

[Install]
WantedBy=timers.target
EOF

echo "✅ systemd timer created: $SERVICE_NAME.timer"

# ─────────────────────────────────────────────
# Enable and start timer
# ─────────────────────────────────────────────
systemctl --user daemon-reload
systemctl --user enable --now "$SERVICE_NAME.timer"

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
echo "  systemctl --user status $SERVICE_NAME.timer"
echo ""
echo "To view next run:"
echo "  systemctl --user list-timers | grep $SERVICE_NAME"
echo ""
echo "To uninstall:"
echo "  systemctl --user disable --now $SERVICE_NAME.timer"
echo "  rm $SERVICE_DIR/$SERVICE_NAME.service $SERVICE_DIR/$SERVICE_NAME.timer"
echo "  systemctl --user daemon-reload"
