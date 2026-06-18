#!/usr/bin/env python3
"""
Cross-platform auto-start installer for Job Tracker daily email check.

Detects the operating system and runs the appropriate setup script:
  - Windows: setup_autostart.ps1 (Task Scheduler)
  - macOS:   setup_autostart_macos.sh (launchd)
  - Linux:   setup_autostart_linux.sh (systemd user timer)

Usage:
    python setup_autostart.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    project_dir = Path(__file__).parent.absolute()

    scripts = {
        "win32":  project_dir / "setup_autostart.ps1",
        "darwin": project_dir / "setup_autostart_macos.sh",
    }

    # Linux detection (many platform strings)
    if sys.platform.startswith("linux"):
        script = project_dir / "setup_autostart_linux.sh"
    else:
        script = scripts.get(sys.platform)

    if script is None:
        print(f"❌ Unsupported platform: {sys.platform}")
        print(f"   Supported platforms: Windows, macOS, Linux")
        sys.exit(1)

    if not script.exists():
        print(f"❌ Setup script not found: {script}")
        sys.exit(1)

    print(f"Detected platform: {sys.platform}")
    print(f"Running: {script}")

    if sys.platform == "win32":
        cmd = [
            "powershell",
            "-ExecutionPolicy", "Bypass",
            "-File", str(script),
        ]
    else:
        cmd = ["bash", str(script)]

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
